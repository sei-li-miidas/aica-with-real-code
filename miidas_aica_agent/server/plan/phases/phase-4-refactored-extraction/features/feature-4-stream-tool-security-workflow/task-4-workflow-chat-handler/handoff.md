# 引き継ぎ: task-4-workflow-chat-handler

## 概要

`WorkflowChatHandler` を新規作成し、`chat_service_refactored.py` の `job_type_decided`、`clear_jobtype`、
`workflow_submitted`、`workflow_cancelled` を `WorkflowChatHandler` による前処理 + `self.chat()` 委譲に
切り替えた。テスト側では `test_workflow_side_effects.py` の `real-refactored` バリアントを unlock し、
`rollback_security` 42 passed を達成した。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat/workflow_chat_handler.py` | 新規作成。`WorkflowChatHandler` クラス。`prepare_job_type_decided` / `prepare_clear_jobtype` / `prepare_workflow_submitted` / `prepare_workflow_cancelled` インターフェース。`WorkflowChatHandlerResult` 値オブジェクト。 |
| `server/src/aica_agent/services/chat_service_refactored.py` | `WorkflowChatHandler` import 追加。`__init__` に `_workflow_chat_handler` 生成を追加。`job_type_decided` / `clear_jobtype` / `workflow_submitted` / `workflow_cancelled` を legacy 委譲から `WorkflowChatHandler` 前処理 + `self.chat()` 委譲に変更。 |
| `server/tests/unit/services/chat/test_workflow_chat_handler.py` | 新規作成。`WorkflowChatHandler` の unit tests（100% branch coverage、32 tests）。 |
| `server/tests/integration/chat_service_contract/conftest.py` | `chat_service_container_workflow` フィクスチャを追加（legacy / delegating-refactored / real-refactored 全 3 variant サポート）。 |
| `server/tests/integration/chat_service_contract/test_workflow_side_effects.py` | `real-refactored` variants の skip を除去。`chat_service_container_workflow` フィクスチャへ切り替え。`_setup_runner_mock` / `_make_normalized_text_delta` ヘルパー追加。`non_local_env` に `services.chat_service_refactored.is_local_or_dev` パッチを追加。 |

## 新しいAPI / ヘルパー / フィクスチャ

### `WorkflowChatHandlerResult`（値オブジェクト）

```python
class WorkflowChatHandlerResult:
    error_response: ChatStreamResponseModel | None
    prepared_message: str | None
```

### `WorkflowChatHandler`（`services/chat/workflow_chat_handler.py`）

```python
class WorkflowChatHandler:
    def __init__(
        self,
        position_service: PositionService,
        workflow_service: WorkflowService,
        llm_service: LLMService,
        get_agents: Callable,
        get_provider: Callable,
        save_chat_histories: Callable,
        get_active_agent_name: Callable,
    ): ...
    async def prepare_job_type_decided(input: ChatRequestModel) -> WorkflowChatHandlerResult: ...
    async def prepare_clear_jobtype(input: ChatRequestModel) -> WorkflowChatHandlerResult: ...
    async def prepare_workflow_submitted(input: ChatRequestModel) -> WorkflowChatHandlerResult: ...
    async def prepare_workflow_cancelled(input: ChatRequestModel) -> WorkflowChatHandlerResult: ...
```

### テストフィクスチャ

- `chat_service_container_workflow`: ワークフロー副作用テスト専用の 3-variant フィクスチャ（legacy / delegating-refactored / real-refactored）
- `_setup_runner_mock(variant, chat_svc, svc, events_sdk, events_normalized)`: variant に応じてランナーモックを設定するヘルパー
- `_make_normalized_text_delta(item_id, delta)`: real-refactored 向けの正規化済みイベント生成

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| `WorkflowChatHandlerResult` 値オブジェクトを導入 | `error_response` と `prepared_message` の 2 つの状態をまとめて返し、呼び出し元が分岐処理しやすくする | タプルで返す（可読性が下がる）、例外で伝える（フロー制御が複雑になる） |
| `get_agents` / `get_provider` をコールバックとして渡す | `init_session()` 後に legacy._agents / legacy._provider が確定するため、生成時ではなく呼び出し時に取得する必要がある | 生成時に値コピー（init_session 前に生成される可能性がある） |
| `save_chat_histories` コールバックを `WorkflowChatHandler.__init__` で受け取り、`prepare_workflow_submitted()` 内で呼ぶ設計 | `workflow_submitted` の履歴保存は WorkflowChatHandler が担うことで呼び出し元（`chat_service_refactored`）の責務を「委譲」に限定した | caller（`chat_service_refactored.workflow_submitted`）で保存する（WorkflowChatHandler の責務が「準備」のみになり呼び出し元が副作用の順序管理も担う） |
| `AttributeError` も捕捉対象に追加 | `json.loads("null")` が `None` を返し、`None.get()` が `AttributeError` を上げるケースを安全に処理するため | `TypeError` のみ捕捉（`None.get()` は `AttributeError` なので捕捉できない） |

## 互換性メモ

- `chat_service_refactored.py` の `job_type_decided` / `clear_jobtype` / `workflow_submitted` / `workflow_cancelled` は引き続き public API として維持される
- `WorkflowChatHandler` は `chat_service_refactored.__init__` 内で生成されるため、既存の DI 構成に変更なし
- legacy `ChatService` の workflow メソッドには一切変更なし（change-minimal 方針遵守）
- `chat_service_container` フィクスチャは変更なし（`real-refactored` の skip は維持）。workflow tests は `chat_service_container_workflow` フィクスチャを使用

## 次タスクへのフォローアップ

- task-5 (legacy-dependency-removal): `chat_service_refactored.py` が legacy を `_delegate_chat=False` 時に完全に使わずに動作することの検証。`_workflow_chat_handler` 経由のワークフロー処理も legacy-free になった。

## 未解決の質問

- なし

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
