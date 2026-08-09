from repositories.agent_repo import AgentRepository
from repositories.prompt_repo import PromptRepository
from domain.entities.agent import Agent
from services.base_service import BaseService


class AgentService(BaseService):
    """エージェント関連の操作を行うサービス。AgentRepositoryとPromptRepositoryを連携する"""

    def __init__(
        self,
        agent_repository: AgentRepository,
        prompt_repository: PromptRepository,
    ) -> None:
        """
        AgentServiceを初期化する

        Args:
            agent_repository: エージェントのデータベース操作用リポジトリ
            prompt_repository: プロンプトのファイル操作用リポジトリ
        """
        super().__init__()
        self._agent_repository = agent_repository
        self._prompt_repository = prompt_repository

    def get_agents_with_prompts(self) -> list[tuple[Agent, str]]:
        """
        全てのエージェントとそのプロンプト（ファイルから読み込み）を取得する

        Returns:
            (Agent, プロンプト内容)のタプルのリスト

        Raises:
            FileNotFoundError: プロンプトファイルが欠落している場合
        """
        # データベースから全てのエージェントを取得
        agents = self._agent_repository.get_agents()
        self.logger.info(
            "データベースから%s個のエージェントを読み込みました", len(agents)
        )

        # 全てのプロンプトファイルが存在することを検証（フェイルファスト）
        self._prompt_repository.validate_all_prompts(agents)

        # 各エージェントのプロンプトを読み込む
        agents_with_prompts = []
        for agent in agents:
            prompt = self._prompt_repository.get_prompt(agent.id, agent.name)
            agents_with_prompts.append((agent, prompt))

        self.logger.info(
            "%s個のエージェントのプロンプトを正常に読み込みました",
            len(agents_with_prompts),
        )
        return agents_with_prompts
