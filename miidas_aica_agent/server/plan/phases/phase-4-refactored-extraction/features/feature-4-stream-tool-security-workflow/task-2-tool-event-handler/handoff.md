# 引き継ぎ: task-2-tool-event-handler

## 概要

`ToolEventHandler` を `server/src/aica_agent/services/chat/tool_event_handler.py` に新規作成した。
`StreamEventProcessor.process()` に `tool_event_handler` / `client_ip` パラメータを追加し、
`ToolCallItem` / `ToolCallOutputItem` の処理を `ToolEventHandler` へ委譲するようにした。
`chat_service_refactored.py` では `ToolEventHandler` をターンごとに生成し、`process()` へ渡す。
integration test の `real-refactored` バリアントが `pending-phase-4` スキップから解除され、
`tool result response shape` の real-refactored evidence が pass になった。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat/tool_event_handler.py` | 新規作成。ToolEventHandler クラスと関連ヘルパー関数。 |
| `server/src/aica_agent/services/chat/stream_event_processor.py` | `process()` に `tool_event_handler: ToolEventHandler | None = None` と `client_ip: str = ""` を追加。ToolCallItem / ToolCallOutputItem を tool_event_handler へ委譲。 |
| `server/src/aica_agent/services/chat_service_refactored.py` | `ToolEventHandler` / `PositionSearchRateLimitExceeded` import 追加。ターンごとに `_current_tool_event_handler` を生成し `process()` に渡す。`_append_stop_at_tool_outputs_callback` を `build_stop_at_tool_outputs()` 経由に変更。legacy フォールバック実装を `_append_stop_at_tool_outputs_legacy()` として分離。`PositionSearchRateLimitExceeded` を generic `Exception` より先に catch して rate-limit 専用メッセージを返すよう修正。 |
| `server/tests/unit/services/chat/test_tool_event_handler.py` | 新規作成。51 テスト、branch coverage 100%。 |
| `server/tests/integration/chat_service_contract/conftest.py` | `chat_service_container_tool_results` フィクスチャを追加（real-refactored 含む 3 variant 対応）。 |
| `server/tests/integration/chat_service_contract/test_tool_results.py` | フィクスチャを `chat_service_container_tool_results` に変更し real-refactored を解除。`_setup_runner_mock()` ローカルヘルパーで variant 別の runner モック設定を吸収（`chat_service_contract_helpers.py` ではなく `test_tool_results.py` 内に定義）。 |

## 新しいAPI / ヘルパー / フィクスチャ

### ToolEventHandler

```python
class ToolEventHandler:
    def __init__(
        self,
        position_repository: PositionRepository,
        rate_limit_service: RateLimitService,
        workflow_service: WorkflowService,
    ) -> None: ...

    def reset(self) -> None:
        """ターン開始時にツールコール状態（_tool_calls / _position_search_counts）をリセットする。"""

    async def handle_tool_call(self, item: ToolCallItem, client_ip: str) -> None:
        """ToolCallItem を記録し、position search の場合は rate limit を確認する。"""

    async def handle_tool_output(
        self,
        item: ToolCallOutputItem,
        chat_response: ChatStreamResponse,
        session_status: ChatSessionStatus,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """ToolCallOutputItem を処理し POSITION_SEARCH_RESULT / JOBTYPE_SEARCH_RESULT / WORKFLOW を yield する。"""

    def build_stop_at_tool_outputs(
        self,
        tool_replay_items: list[dict[str, Any]],
        stop_at_tool_exists: bool,
    ) -> list[dict[str, Any]]:
        """stop_at_tool 発生時に次ターンへ渡す function_call_output リストを返す（caller が conversation に追加する）。"""
```

### StreamEventProcessor.process() 変更

```python
async def process(
    self,
    run_stream: LLMRunStream,
    chat_response: ChatStreamResponse,
    session_status: ChatSessionStatus,
    tool_event_handler: ToolEventHandler | None = None,  # 追加
    client_ip: str = "",                                  # 追加
) -> AsyncGenerator[ChatStreamResponseModel, None]: ...
```

`tool_event_handler=None` の場合は task-1 相当の動作（ToolCallItem / ToolCallOutputItem は dispatch しない）。

### test_tool_results.py ローカルヘルパー

```python
def _setup_runner_mock(variant: str, chat_svc, svc, events: list) -> None:
    """variant に応じて runner モックを設定する。
    
    legacy / delegating-refactored: svc._run_streamed に _FakeRunResult(events) を設定。
    real-refactored: chat_svc._llm_runner.run_streamed に _FakeRunStream(events) を設定。
    """
```

`chat_service_contract_helpers.py` は変更していない。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| ToolEventHandler をターンごとに生成（`_current_tool_event_handler`） | テストで `svc._position_repository` が差し替えられた場合に最新値を参照できる。per-turn 状態（`_tool_calls`）のリセットも自然に実現できる。 | `__init__` で 1 回生成して `reset()` を呼ぶ: テストの mock 差し替え問題が残るため却下。 |
| `StreamEventProcessor.process()` の `tool_event_handler` を省略可能（`None = None`）にした | task-1 時点の `StreamEventProcessor` unit tests を最小変更で維持できる。段階的な抽出方針と整合する。 | 必須パラメータ化: unit tests を大幅更新する必要があるため却下。 |
| `ToolEventHandler` の constructor は 3 dependencies のみ（APPLICATION/REGISTRATION 省略） | 現在の parity suite に APPLICATION/REGISTRATION tool 専用のシナリオがない。`chat_repository` / `user_repository` を注入すると constructor が複雑になる。 | 全 dependencies を追加: 現時点では不要な complexity のため見送り。task-3 以降で必要になれば追加する。 |
| `is_stop_at_tool` コールバックを `StreamEventProcessor.__init__` に残した | `_is_stop_at_tool` は `chat_service_refactored.ChatService` に残しており、callback として渡す既存設計を維持する。ToolEventHandler 依存なしでも動作する。 | ToolEventHandler.is_stop_at_tool() を呼ぶ: StreamEventProcessor が ToolEventHandler に強く依存することになるため、今の段階では過剰。 |

## 互換性メモ

- `pre_extraction_parity` は 179 passed（前回 173 → +6、tool result real-refactored 3 テスト解除）。
- `rollback_runner` は 32 passed（前回 29 → +3、tool result real-refactored 3 テスト解除）。
- `StreamEventProcessor` の既存 unit tests は `tool_event_handler=None` で引き続き pass。
- `_append_stop_at_tool_outputs_callback` の動作は legacy フォールバックと `build_stop_at_tool_outputs()` 経由の 2 パスになっているが、ターン中に `_current_tool_event_handler` が設定されていれば必ず `build_stop_at_tool_outputs()` が使われる。

## 次タスクへのフォローアップ

- task-3-stream-guard-security: `StreamEventProcessor` の `raw_response_event` ブランチを `StreamGuard` に委譲する。`process()` に `handle_raw_response` コールバックを追加して差し替える。
- task-3 で `_is_stop_at_tool` コールバックを `ToolEventHandler.is_stop_at_tool()` に統合することを検討してよい。
- APPLICATION / REGISTRATION tool の side effect（`chat_repository.update_session_status` / `user_repository.update_*`）は、legacy の「POSITION_DETAIL page + CHATTING/APPLYING/REGISTERING は APPLYING へ集約する」ルーティング境界を保つ parity 項目として扱う。Phase 4 extraction 中の段階的移植では constructor を重くしないため `ToolEventHandler` から直接は扱わず、final parity suite と関連テストで既存挙動を固定する。

## 既知の動作差異（parity gap）

これらは task-2 の extraction 範囲で意図的に残した差異、または現在のフェーズで解決不可能な差異である。後続 task で解決するまで、下流で前提にしてはいけない。

| 項目 | 現在の動作 | legacy の動作 | 解決見込み |
| --- | --- | --- | --- |
| ツール実行失敗（`"Message"` キー） | `ToolEventHandler.handle_tool_output()` が warning ログを出して return（yield なし） | `self._conversation[chat_key].append(function_call_output)` + `llm_error = True` でリトライループを起動 | `chat_service_refactored.py` にリトライループを実装する task（task-5 以降）で対応必須。それまではツール失敗時にモデルがリカバリできない。 |
| `_is_stop_at_tool` の所在 | `chat_service_refactored.ChatService._is_stop_at_tool()` として残存（`StreamEventProcessor` に callback として渡す） | `chat_service.ChatService` 内 | task-2 の設計判断として意図的に残した（設計判断表参照）。task-3 で `ToolEventHandler.is_stop_at_tool()` への統合を検討してよい。 |

## 未解決の質問

なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
