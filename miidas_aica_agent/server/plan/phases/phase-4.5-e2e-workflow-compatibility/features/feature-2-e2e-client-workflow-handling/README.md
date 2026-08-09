# フィーチャー: e2e client workflow ハンドリング

## 目的

`e2e/src/aica_client/client/e2e_client.py` に workflow event の受信・contract 検証・pending action dispatch・submit 送信ロジックを追加する。feature-1 で追加された enum と state を使い、`WORKFLOW` event の受信から `WORKFLOW_ANSWERS_SUBMITTED` 送信までの全パスを完成させる。

## 親フェーズ

- フェーズ: phase-4.5-e2e-workflow-compatibility

## スコープ

スコープ内:
- `_validate_ws_event_contract()` への `ChatResponseType.WORKFLOW` branch 追加
- `_validate_history_record()` の許容型に `ChatResponseType.WORKFLOW` を追加
- `_update_state_from_exchange()` への `ChatResponseType.WORKFLOW` branch 追加（JSON parse + `pending_workflow` 設定）
- `_handle_workflow()` 新規追加（workflow answers 自動 submit）
- `_handle_pending_actions()` の先頭への `pending_workflow` dispatch 追加

スコープ外:
- `models.py` の変更（feature-1 の責務）
- workflow cancel path の実装（デフォルトポリシーは常に submit）
- server 側の変更

## 依存関係

- feature-1-e2e-model-contract（`ChatResponseType.WORKFLOW`、`ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED`、`HeadlessState.pending_workflow` が存在すること）

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-contract-validation-updates | `_validate_ws_event_contract()` と `_validate_history_record()` を WORKFLOW 対応に更新する。 | feature-1 task-1 | static lint check | not-started |
| task-2-workflow-receive-dispatch-send | `_update_state_from_exchange()`、`_handle_workflow()`、`_handle_pending_actions()` を実装する。 | task-1 | static lint check; workflow 発火シナリオ e2e 確認; 非発火シナリオ回帰確認 | not-started |

## 完了条件

- `_validate_ws_event_contract()` が `WORKFLOW` payload の `"id"` フィールドを contract として検証する。
- `_validate_history_record()` が `ChatResponseType.WORKFLOW` を許容型として含む。
- `WORKFLOW` event 受信時に `state.pending_workflow` が設定される。
- `_handle_pending_actions()` が `pending_workflow` を優先処理する。
- `_handle_workflow()` が `workflow_answers_submitted` payload を送信し、`workflow_received` / `workflow_submitting` / `workflow_handled` をログに記録する。
- workflow 発火シナリオで e2e run が crash せず継続する。
