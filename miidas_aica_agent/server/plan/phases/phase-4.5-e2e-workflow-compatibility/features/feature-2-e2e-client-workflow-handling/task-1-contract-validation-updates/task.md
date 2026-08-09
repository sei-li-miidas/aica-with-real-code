# タスク: task-1-contract-validation-updates

## 目的

親 feature README の task table で定義された成果を実装する。詳細 scope は親 feature README と親 phase README を source of truth とする。

## 最初に読むコンテキスト

- 親フェーズ README: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/README.md`
- 親フィーチャー README: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/features/feature-2-e2e-client-workflow-handling/README.md`
- 依存タスクの引き継ぎ: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/features/feature-1-e2e-model-contract/task-1-enum-state-extension/handoff.md`
- 変更対象ファイル: `e2e/src/aica_client/client/e2e_client.py`

## スコープ

許可する変更:
- `e2e/src/aica_client/client/e2e_client.py` の `_validate_ws_event_contract()` と `_validate_history_record()` への WORKFLOW 分岐追加（additive のみ）。

許可しない変更:
- `e2e/src/aica_client/models.py`（feature-1 の責務）
- `_update_state_from_exchange()` / `_handle_workflow()` / `_handle_pending_actions()`（task-2 の責務）
- 既存検証ロジックの削除・変更

## 変更対象

| ファイル | 変更内容 |
| --- | --- |
| `e2e/src/aica_client/client/e2e_client.py` | `_validate_ws_event_contract()` に `elif event.response_type == ChatResponseType.WORKFLOW:` branch を追加し、payload が `{"id": <non-empty str>, ...}` であることを確認する。 |
| `e2e/src/aica_client/client/e2e_client.py` | `_validate_history_record()` の許容型 set に `ChatResponseType.WORKFLOW` を追加する。 |

## 依存関係

- feature-1 task-1（`ChatResponseType.WORKFLOW` が `models.py` に存在すること）

## 実装メモ

- `_validate_ws_event_contract()` の WORKFLOW branch は `plan.md` Change Set §7 の実装指示を source of truth とする。
  - `payload = self._parse_json_message(event.message)`
  - `self._require_contract(isinstance(payload, dict) and isinstance(payload.get("id"), str) and payload.get("id") != "", category="websocket_format_invalid", source=source, details="workflow payload must have non-empty string 'id'", actual=payload)`
- `_validate_history_record()` の set に `ChatResponseType.WORKFLOW` を追加する際は、既存の `MESSAGE` / `POSITION_SEARCH_LINK` / `JOBTYPE_SEARCH_RESULT` に揃えた書き方にする。

## 必須テスト

- `cd e2e && ../.venv-e2e/bin/python -m ruff check src/`

## ロールバック確認対象

- 既存の validation 分岐が削除・変更されていないこと。

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
