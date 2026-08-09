import asyncio
from copy import copy, deepcopy
from enum import StrEnum
from typing import Any, Tuple

from dependency_injector import resources

from agents import Agent, ModelSettings, RunContextWrapper, Tool
from agents.mcp import MCPServerStreamableHttp
from agents.mcp.util import MCPUtil
from openai.types.shared import Reasoning

from services.agent_service import AgentService
from services.base_service import BaseService
from utils.enum import ToolName


class NotSupportedModelName(Exception):
    """
    定義されていないモデル
    """

    def __init__(self, message):
        super().__init__(message)


class ToolNotFoundInRepositoryError(Exception):
    """
    DBにツールが存在しない
    """

    def __init__(self, message):
        super().__init__(message)


class AgentName(StrEnum):
    """
    エージェント名
    テーブル[agents]のカラム[name]となります。
    動的にアクティブエージェントを切り替えるときに利用するためソースにも定義しています。
    """

    CAREER_ADVISOR = "CareerAdvisor"
    POSITION_GUIDE = "PositionGuide"
    POSITION_SEARCH = "PositionSearch"
    POSITION_CHANGE_ANALYZE = "PositionChangeAnalyze"


class LLMService(resources.AsyncResource, BaseService):
    # MCP接続を保持するライフサイクルタスク
    _server_task: asyncio.Task | None = None
    # 初期化完了を外部に知らせるシグナル
    _startup_event: asyncio.Event | None = None
    # シャットダウン開始を通知するシグナル
    _shutdown_event: asyncio.Event | None = None
    # ライフサイクル中に検知した例外を保持
    _server_error: BaseException | None = None
    # 実際のMCPサーバーインスタンス
    _mcp_server = None
    _agents: dict[str, dict[str, tuple[Agent, bool]]]
    _all_tools: list[Tool]
    _search_position_agent_names: dict[str, set[str]]

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        BaseService.__init__(self)
        self._server_task = None
        self._startup_event = None
        self._shutdown_event = None
        self._server_error = None
        self._mcp_server = None
        self._agents = {}
        self._all_tools = []
        self._search_position_agent_names = {}

    #   "caller": "/usr/local/lib/python3.12/site-packages/agents/mcp/server.py:347",
    #   "message": "Error cleaning up server: Attempted to exit cancel scope in a different task than it was entered in"
    # 上記エラー発生原因
    # 1. シャットダウン時に DI コンテナが
    # `await self._mcp_server.__aexit__(...)`
    #  -> `agents/mcp/server.py` の `cleanup()`
    #   -> `self.exit_stack.aclose()`
    #    -> `connect()` で入った `streamablehttp_client` のコンテキストをunwind
    # 2. Streamable HTTP コンテキストは `anyio.CancelScope` をラップし、enter した `asyncio.Task` を
    #    記録している。AWS ECS がタスクを停止すると、Starlette のライフスパンシャットダウンが
    #    起動時とは別のタスクで実行される。
    # 4. `anyio` は enter したタスクとは別のタスクから CancelScope を抜けることを禁止しているため、
    #    `RuntimeError("Attempted to exit cancel scope in a different task than it was entered in")`
    #    が発生し、ログに `Error cleaning up server` として出力される。
    async def init(
        self,
        mcp_url: str,
        timeout: float,
        model_list: list,
        agent_svc: AgentService,
    ):
        """
        LLMService初期化
        ・MCPサーバ接続
        ・ワークフロー初期化（エージェントとハンドオフ関係、ツール）

        Args:
            mcp_url: MCPサーバーURL
            timeout: MCP接続タイムアウト
            model_list: LLMモデル一覧
            agent_svc: エージェントサービス
        """
        self._mcp_server = MCPServerStreamableHttp(
            name="AICA Server",
            params={
                "url": mcp_url,
            },
            client_session_timeout_seconds=timeout,
            max_retry_attempts=5,
        )
        self._startup_event = asyncio.Event()
        self._shutdown_event = asyncio.Event()
        self._server_error = None
        try:
            if self._server_task and not self._server_task.done():
                raise RuntimeError("MCPサーバーライフサイクルは既に起動しています。")
            self._server_task = asyncio.create_task(
                self._mcp_server_lifecycle(mcp_url),
                name="mcp-server-lifecycle",
            )
            await self._startup_event.wait()
            if self._server_error:
                raise self._server_error

            self._all_tools = await MCPUtil.get_all_function_tools(
                [self._mcp_server], True, RunContextWrapper(context=None), None
            )

            agent_models = [
                model for model in model_list if "agent" in model["use_for"]
            ]
            if not agent_models:
                raise Exception("Agent用のモデルが定義されていません")

            await self._init_agents(agent_models, agent_svc)

        except Exception:
            self.logger.exception("Agent初期化失敗（MCPサーバー： %s）", mcp_url)

            # ライフサイクルタスクを待機してコンテキストを確実に閉じる
            if self._shutdown_event and not self._shutdown_event.is_set():
                self._shutdown_event.set()
            if self._server_task:
                await asyncio.gather(self._server_task, return_exceptions=True)

            raise

        return self

    async def shutdown(self, _: None):
        """
        LLMService終了処理
        ・MCPサーバ切断
        """
        if self._server_task is None:
            self.logger.info("MCPサーバがないので、接続切断は不要")
            return

        assert self._shutdown_event is not None
        self._shutdown_event.set()
        await self._server_task
        self._server_task = None
        self._mcp_server = None

        if self._server_error:
            raise self._server_error
        else:
            self.logger.info("MCPサーバとの接続を正常に切断しました。")

    async def _mcp_server_lifecycle(
        self,
        mcp_url: str,
    ):
        """
        MCPサーバーのコンテキストを単一タスクで管理するライフサイクルラッパー。
        enter/exit を同じタスクで実行し anyio の cancel scope 制約を満たす。
        """
        if self._mcp_server is None:
            raise RuntimeError("MCPサーバーが初期化されていません。")

        try:
            # streamablehttp_clientはasynccontextmanagerなので、
            # async with self._mcp_serverは一般的な使い方ですが、
            # MCP接続失敗の際に、__aexit__が呼ばれず、他のタスクより停止してcleanupに入ります。
            # そのため、依然として
            # RuntimeError("Attempted to exit cancel scope in a different task than it was entered in")
            # が発生します。したがって、async with構文は使わず、connectとcleanupを直接呼び出しています。
            await self._mcp_server.connect()

            assert self._startup_event is not None
            self._startup_event.set()
            assert self._shutdown_event is not None
            await self._shutdown_event.wait()
        except BaseException as exc:
            self._server_error = exc
            if self._startup_event and not self._startup_event.is_set():
                self._startup_event.set()
            self.logger.exception("Agent初期化失敗（MCPサーバー： %s）", mcp_url)
        finally:
            # FIXME: ローカルのみかもしれないが、MCPサーバへの接続が切れた場合（MCPサーバダウンとかのため）
            # asyncio.CancelledError (BaseException)が発生するため、ここに来てしまい
            # MCPサーバへの接続がなくなります。そのため、それ以降はMCPツールが使えなくなります。
            # なので、再接続するロジックが必要。
            # それとも、Streamable HTTP (SSE利用なし)なので、shutdownの場合のみcleanupを実施して、
            # エラーが発生した場合cleanupしないほうが良いかも
            try:
                await self._mcp_server.cleanup()
            except RuntimeError as cleanup_error:
                message = str(cleanup_error)
                if "Attempted to exit cancel scope" in message:
                    self.logger.warning(
                        "CancelScopeの制約によりMCPサーバーのクリーンアップでRuntimeErrorを無視します。",
                        exc_info=True,
                    )
                else:
                    self.logger.exception(
                        "MCPサーバークリーンアップ中に例外発生",
                    )
            except Exception:
                self.logger.exception(
                    "MCPサーバークリーンアップ中に想定外の例外が発生",
                )

            # 例外発生時でも待機中コルーチンが進行できるようにする
            if self._shutdown_event and not self._shutdown_event.is_set():
                self._shutdown_event.set()
            if self._startup_event and not self._startup_event.is_set():
                self._startup_event.set()

    async def _init_agents(
        self,
        model_list: list[dict[str, Any]],
        agent_svc: AgentService,
    ):
        """
        src/aica_agent/config.ymlの[model_list]をもとにワークフロー初期化（エージェントとハンドオフ関係、ツール）

        Args:
            model_list: LLMモデル一覧。src/aica_agent/config.ymlの[model_list]
            agent_svc: エージェントサービス（エージェント設定とプロンプト）
        """
        tool_names = [tool.name for tool in self._all_tools]
        self.logger.debug("MCP Tools: %s", tool_names)

        # Get agents with prompts from AgentService
        agents_with_prompts = agent_svc.get_agents_with_prompts()

        for model in model_list:
            model_name = model["model"]
            raw_settings = deepcopy(model["model_settings"])
            reasoning = raw_settings.get("reasoning")
            if isinstance(reasoning, dict):
                raw_settings["reasoning"] = Reasoning.model_validate(reasoning)
            model_settings = ModelSettings(
                **raw_settings,
            )
            react_agents = {}
            search_position_agent_names: set[str] = set()
            for agent, prompt in agents_with_prompts:
                self.logger.debug(
                    "Agent %sのシステムプロンプト: %s",
                    agent.name,
                    prompt,
                )

                agent_tool_names = [agent_tool.tool_name for agent_tool in agent.tools]
                non_existent_tools = [
                    tool_name
                    for tool_name in agent_tool_names
                    if tool_name not in tool_names
                ]
                if non_existent_tools:
                    # DBに定義があるがMCPサーバーにツールが存在しない場合、起動エラー
                    self.logger.error(
                        "Agent %sのツール%sがMCPサーバーに存在しない。",
                        agent.name,
                        non_existent_tools,
                    )
                    raise ToolNotFoundInRepositoryError(
                        f"Agent {agent.name}のツール{non_existent_tools}がMCPサーバーに存在しない。"
                    )
                agent_tools = [
                    tool for tool in self._all_tools if tool.name in agent_tool_names
                ]
                if agent.can_search_position:
                    search_position_agent_names.add(agent.name)

                react_agent = Agent(
                    model=model_name,
                    model_settings=model_settings,
                    name=agent.name,
                    instructions=prompt,
                    tools=agent_tools,
                )
                stop_at_tool_names = [
                    tool.tool_name for tool in agent.tools if tool.return_direct
                ]
                if stop_at_tool_names:
                    react_agent.tool_use_behavior = {
                        "stop_at_tool_names": stop_at_tool_names,
                    }

                react_agents[agent.name] = (
                    react_agent,
                    agent.next_agents,
                    agent.default_agent,
                )

            for _, (agent, next_agents, _) in react_agents.items():
                if next_agents:
                    agent.handoffs = [
                        react_agents[next_agent.dest_agent.name][0]
                        for next_agent in next_agents
                    ]

            self._agents[model_name] = {
                agent_name: (agent, default_agent)
                for agent_name, (agent, _, default_agent) in react_agents.items()
            }
            self._search_position_agent_names[model_name] = search_position_agent_names

    def clone_agents(
        self,
        model_name: str,
        jobtype_names: str | list[str] | None = None,
        tool_name: str | None = None,
    ) -> dict[str, Tuple[Agent, bool]]:
        """
        エージェント群をクローンする。

        Args:
            model_name: LLMモデルネーム
            jobtype_names: 現在選択中職種名一覧（まだない可能性がある）

        Returns:
            エージェント群
        """
        if model_name not in self._agents:
            self.logger.error("Unsupported model name: %s", model_name)
            raise NotSupportedModelName(f"Unsupported model name: {model_name}")

        # https://miidas-dev.slack.com/archives/C08CPHXCZ08/p1750994467102159
        # 性能面（あくまで推測、負荷テストで確認する必要があります）やThread-safeから考えると、
        # グローバル１つのAgentではなく、セッションごとに各自のAgentを持つ
        cloned_agents = {
            k: (v[0].clone(), v[1]) for k, v in self._agents[model_name].items()
        }

        normalized_jobtype_names = self._normalize_job_type_names(jobtype_names)
        normalized_tool_name = tool_name.strip() if isinstance(tool_name, str) else ""
        if not normalized_tool_name:
            return cloned_agents

        configured_tool = self._build_position_search_tool(
            normalized_tool_name,
            normalized_jobtype_names,
        )
        if not configured_tool:
            self.logger.error(
                "Failed to configure position search tool in clone_agents (model=%s, jobtypes=%s)",
                model_name,
                normalized_jobtype_names,
            )
            return cloned_agents

        target_agent_names = self._search_position_agent_names.get(model_name, set())
        for target_agent_name in target_agent_names:
            if target_agent_name not in cloned_agents:
                self.logger.error(
                    "Target agent for position search is missing in cloned agents (model=%s, agent=%s)",
                    model_name,
                    target_agent_name,
                )
                continue
            cloned_agent = cloned_agents[target_agent_name][0]
            self._set_position_search_tool(cloned_agent, configured_tool)

        return cloned_agents

    def update_agent_by_tool_name(
        self,
        model_name: str,
        tool_name: str | None,
        job_type_names: list[str] | None = None,
        target_agents: dict[str, Agent] | None = None,
    ) -> tuple[dict[str, Agent] | None, str | None]:
        """
        指定ツールをエージェントに適用する。tool_name が None の場合はポジション検索ツールを解除する。
        MCP サーバーが当該ツールを提供していない場合は (None, None) を返す。
        """
        if model_name not in self._agents:
            raise NotSupportedModelName(f"Unsupported model name: {model_name}")

        target_agent_names = self._search_position_agent_names.get(model_name, set())
        if not target_agent_names:
            return None, None

        if not tool_name:
            updated_agents = self._update_position_search_agents(
                model_name,
                target_agent_names,
                target_agents,
                None,
            )
            return updated_agents, None

        tool = self._build_position_search_tool(tool_name, job_type_names)
        if not tool:
            return None, None

        updated_agents = self._update_position_search_agents(
            model_name,
            target_agent_names,
            target_agents,
            tool,
        )
        return updated_agents, tool.name

    def _update_position_search_agents(
        self,
        model_name: str,
        target_agent_names: set[str],
        target_agents: dict[str, Agent] | None,
        tool: Tool | None,
    ) -> dict[str, Agent]:
        updated_agents: dict[str, Agent] = {}
        for target_agent_name, target_agent in self._iter_target_position_agents(
            model_name,
            target_agent_names,
            target_agents,
        ):
            self._set_position_search_tool(target_agent, tool)
            updated_agents[target_agent_name] = target_agent
        return updated_agents

    def _iter_target_position_agents(
        self,
        model_name: str,
        target_agent_names: set[str],
        target_agents: dict[str, Agent] | None,
    ):
        for target_agent_name in target_agent_names:
            if target_agents is not None:
                if target_agent_name not in target_agents:
                    continue
                yield target_agent_name, target_agents[target_agent_name]
                continue

            if target_agent_name not in self._agents[model_name]:
                continue
            yield target_agent_name, self._agents[model_name][target_agent_name][0]

    def _set_position_search_tool(self, target_agent: Agent, tool: Tool | None) -> None:
        # 既存ポジション検索ツールをAgentから削除
        target_agent.tools = [
            existing_tool
            for existing_tool in target_agent.tools
            if not ToolName.is_position_search_tool(existing_tool.name)
        ]

        if tool is not None:
            # 新しいポジション検索ツールをAgentに登録
            target_agent.tools.append(tool)

        behavior = self._normalize_tool_use_behavior(target_agent.tool_use_behavior)
        stop_at_tool_names = list(behavior.get("stop_at_tool_names", []))
        # 既存ポジション検索ツール削除
        filtered_stop_at_tool_names = [
            existing_tool_name
            for existing_tool_name in stop_at_tool_names
            if not ToolName.is_position_search_tool(existing_tool_name)
        ]
        if tool is not None and tool.name not in filtered_stop_at_tool_names:
            filtered_stop_at_tool_names.append(tool.name)
        if filtered_stop_at_tool_names != stop_at_tool_names:
            behavior["stop_at_tool_names"] = filtered_stop_at_tool_names
            target_agent.tool_use_behavior = behavior

    def _build_position_search_tool(
        self, tool_name: str, job_type_names: list[str] | None = None
    ) -> Tool | None:
        if not ToolName.is_position_search_tool(tool_name):
            self.logger.error("Unsupported position search tool: %s", tool_name)
            return None

        tool = self._find_tool_by_name(tool_name)
        if not tool:
            self.logger.error(
                "Position search tool %s is not supported by MCP server", tool_name
            )
            return None

        normalized_job_type_names = self._normalize_job_type_names(job_type_names)

        # toolにはMCPクライアントの接続情報が含まれており、その中にasyncio.Futureが含まれているためdeepcopyできない
        # そのため、shallow copyを作成し、変更が必要なparams_json_schemaのみdeepcopyする
        tool = copy(tool)
        tool.params_json_schema = deepcopy(tool.params_json_schema)
        if normalized_job_type_names:
            selected_names = "、".join(normalized_job_type_names)
            tool.description = (
                f"{tool.description}\n\n"
                f"JobtypeNames には選択済みの全職種をそのまま含めてください: {selected_names}。ただし、ユーザーが検索したい職種や除外したい職種を明示した場合はその指示を優先してください。"
            )
        if normalized_job_type_names and "properties" in tool.params_json_schema:
            tool.params_json_schema["properties"]["JobtypeNames"] = {
                "type": "array",
                "items": {"enum": normalized_job_type_names, "type": "string"},
            }
            # https://platform.openai.com/docs/guides/structured-outputs#all-fields-must-be-required
            required = tool.params_json_schema.get("required")
            if isinstance(required, list):
                if "JobtypeNames" not in required:
                    required.append("JobtypeNames")
            else:
                tool.params_json_schema["required"] = list(
                    tool.params_json_schema["properties"].keys()
                )

        return tool

    def _normalize_job_type_names(
        self, job_type_names: str | list[str] | None
    ) -> list[str]:
        if job_type_names is None:
            return []
        if isinstance(job_type_names, str):
            names = [job_type_names]
        else:
            names = job_type_names

        normalized_names: list[str] = []
        seen: set[str] = set()
        for job_type_name in names:
            normalized_name = job_type_name.strip()
            if not normalized_name or normalized_name in seen:
                continue
            seen.add(normalized_name)
            normalized_names.append(normalized_name)
        return normalized_names

    def _find_tool_by_name(self, tool_name: str) -> Tool | None:
        return next((tool for tool in self._all_tools if tool.name == tool_name), None)

    def _normalize_tool_use_behavior(self, behavior: Any) -> dict[str, Any]:
        if behavior is None:
            return {}
        if isinstance(behavior, dict):
            return dict(behavior)
        if hasattr(behavior, "model_dump"):
            dumped = behavior.model_dump()
            if isinstance(dumped, dict):
                return dumped
        if hasattr(behavior, "to_dict"):
            dumped = behavior.to_dict()
            if isinstance(dumped, dict):
                return dumped

        self.logger.warning(
            "Unexpected tool_use_behavior type: %s. Fallback to empty dict.",
            type(behavior).__name__,
        )
        return {}
