# フィーチャー: e2e model contract 拡張

## 目的

`e2e/src/aica_client/models.py` に workflow 系の enum 値と state フィールドを追加し、Phase 4 の refactored 実体が emit する `WORKFLOW` response と、e2e が送信する必要がある workflow request types を Pydantic model が受理できる状態にする。

## 親フェーズ

- フェーズ: phase-4.5-e2e-workflow-compatibility

## スコープ

スコープ内:
- `ChatResponseType` への `WORKFLOW = "workflow"` 追加
- `ChatRequestType` への `WORKFLOW_ANSWERS_SUBMITTED = "workflow_answers_submitted"` および `WORKFLOW_CANCELLED = "workflow_cancelled"` 追加
- `HeadlessState` への `pending_workflow: dict[str, Any] | None = None` フィールド追加

スコープ外:
- `e2e_client.py` の変更（feature-2 の責務）
- server 側の変更

## 依存関係

- Phase 4 完了

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-enum-state-extension | `ChatResponseType.WORKFLOW`、workflow request types、`HeadlessState.pending_workflow` を `models.py` に追加する。 | Phase 4 完了 | static lint check; `model_validate_json` smoke check | not-started |

## 完了条件

- `ChatResponseType.WORKFLOW == "workflow"` が成立する。
- `ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED == "workflow_answers_submitted"` および `ChatRequestType.WORKFLOW_CANCELLED == "workflow_cancelled"` が成立する。
- `HeadlessState` に `pending_workflow: dict[str, Any] | None = None` フィールドが存在する。
- `ChatStreamResponseModel.model_validate_json('{"response_type": "workflow", ...}')` が Pydantic validation error を出さない。
