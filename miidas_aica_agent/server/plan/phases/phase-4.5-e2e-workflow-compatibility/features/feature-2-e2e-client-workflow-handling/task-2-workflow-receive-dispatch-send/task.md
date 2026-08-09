# タスク: task-2-workflow-receive-dispatch-send

## 目的

親 feature README の task table で定義された成果を実装する。詳細 scope は親 feature README と親 phase README を source of truth とする。

## 最初に読むコンテキスト

- 親フェーズ README: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/README.md`
- 親フィーチャー README: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/features/feature-2-e2e-client-workflow-handling/README.md`
- 依存タスクの引き継ぎ: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/features/feature-2-e2e-client-workflow-handling/task-1-contract-validation-updates/handoff.md`
- 変更対象ファイル: `e2e/src/aica_client/client/e2e_client.py`

## スコープ

許可する変更:
- `e2e/src/aica_client/client/e2e_client.py` の以下 3 点（additive / minimal targeted change のみ）。

許可しない変更:
- `e2e/src/aica_client/models.py`（feature-1 の責務）
- `_validate_ws_event_contract()` / `_validate_history_record()`（task-1 の責務）
- 既存 dispatch ロジックの削除・変更

## 変更対象

| ファイル | 変更内容 |
| --- | --- |
| `e2e/src/aica_client/client/e2e_client.py` | `_update_state_from_exchange()` の `for event in exchange.events:` ループに `elif event.response_type == ChatResponseType.WORKFLOW:` branch を追加し、`self._parse_json_message(event.message)` の結果を `self.state.pending_workflow` に設定する。 |
| `e2e/src/aica_client/client/e2e_client.py` | `async def _handle_workflow(self, workflow: dict[str, Any]) -> None` を新規追加する。`plan.md` Change Set §5 の実装指示を source of truth とする。 |
| `e2e/src/aica_client/client/e2e_client.py` | `_handle_pending_actions()` の先頭（既存 `if self.state.pending_jobtype_search:` の前）に `if self.state.pending_workflow:` dispatch を追加する。`_handle_pending_actions()` は async メソッドであり、`await self._handle_workflow(pending)` として呼び出す。 |

## 依存関係

- feature-2 task-1（`_validate_ws_event_contract()` と `_validate_history_record()` の WORKFLOW 対応が完了していること）

## 実装メモ

`_handle_workflow()` の実装指示（`plan.md` Change Set §5 より）:

**シグネチャ: `async def _handle_workflow(self, workflow: dict[str, Any]) -> None`**（`_send_ws_action()` が async のため、このメソッドも async にする。`_handle_pending_actions()` から `await self._handle_workflow(pending)` として呼び出す）。
1. `workflow_id = workflow["id"]`
2. `self._log_action("workflow_received", workflow_id=workflow_id)`
3. 各 step の最初のオプション値を選択して answers dict を構築する。
   - `step["options"]` の各エントリが `"items"` を持つ場合は `items[0]["value"]`、持たない場合は `option["value"]` を使用する。
   - answer format: `{str(step["id"]): [first_value]}`
4. `self._log_action("workflow_submitting", workflow_id=workflow_id, step_count=len(answers))`
5. `_build_chat_payload()` で `WORKFLOW_ANSWERS_SUBMITTED` payload を組み立て、`_send_ws_action()` で送信する。
   - `message=json.dumps({"workflow_id": workflow_id, "answers": answers}, ensure_ascii=False)`
6. `self._log_action("workflow_handled", workflow_id=workflow_id)`

`_handle_pending_actions()` への dispatch（`plan.md` Change Set §6 より）:
```python
if self.state.pending_workflow:
    pending = self.state.pending_workflow
    self.state.pending_workflow = None
    await self._handle_workflow(pending)
    return True
```

## 必須テスト

- `cd e2e && ../.venv-e2e/bin/python -m ruff check src/`
- workflow 発火シナリオを含む e2e run での確認（`./e2e/start_test.sh` を local server に対して実行）
- workflow 非発火シナリオでの回帰確認

## ロールバック確認対象

- workflow 非発火シナリオで既存 pending action dispatch（jobtype, position search）が退行しないこと。
- `_handle_pending_actions()` の return 値が既存と互換であること（dispatch 済みの場合 `True`、未 dispatch の場合は既存フロー継続）。

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`。
- workflow 発火シナリオで e2e run が crash せず `workflow_handled` がログに記録されることを手動確認し、`verification.md` の手動確認欄に結果を記入する。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
