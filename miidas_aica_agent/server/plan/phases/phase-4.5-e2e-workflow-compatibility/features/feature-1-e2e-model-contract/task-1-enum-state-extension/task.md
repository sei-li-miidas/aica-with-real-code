# タスク: task-1-enum-state-extension

## 目的

親 feature README の task table で定義された成果を実装する。詳細 scope は親 feature README と親 phase README を source of truth とする。

## 最初に読むコンテキスト

- 親フェーズ README: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/README.md`
- 親フィーチャー README: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/features/feature-1-e2e-model-contract/README.md`
- 変更対象ファイル: `e2e/src/aica_client/models.py`

## スコープ

許可する変更:
- `e2e/src/aica_client/models.py` への enum 値と state フィールドの追加（additive のみ）。

許可しない変更:
- `e2e/src/aica_client/client/e2e_client.py`（feature-2 の責務）
- server 側のファイル
- 既存 enum 値の変更や削除

## 変更対象

| ファイル | 変更内容 |
| --- | --- |
| `e2e/src/aica_client/models.py` | `ChatResponseType` に `WORKFLOW = "workflow"` を追加する。 |
| `e2e/src/aica_client/models.py` | `ChatRequestType` に `WORKFLOW_ANSWERS_SUBMITTED = "workflow_answers_submitted"` と `WORKFLOW_CANCELLED = "workflow_cancelled"` を追加する。 |
| `e2e/src/aica_client/models.py` | `HeadlessState` に `pending_workflow: dict[str, Any] | None = None` を追加する（他の `pending_*` フィールドに揃える）。 |

## 依存関係

- Phase 4 完了

## 実装メモ

- `ChatResponseType` の enum 値追加は `ERROR` と `END` の前に挿入するか末尾に追加するかはファイルの既存順序に倣う。
- `HeadlessState` への `Any` 型参照には `from typing import Any` がすでに import されているか確認し、なければ追加する。
- `pending_workflow` フィールドは他の `pending_position_search_result` / `pending_position_search_link` / `pending_jobtype_search` と同じ pattern で追加する。

## 必須テスト

- `cd e2e && ../.venv-e2e/bin/python -m ruff check src/`
- `cd e2e && PYTHONPATH=src/aica_client ../.venv-e2e/bin/python -c "from models import ChatStreamResponseModel; m = ChatStreamResponseModel.model_validate_json('{\"response_type\": \"workflow\", \"message\": \"{}\", \"message_id\": \"test\"}'); assert m.response_type == 'workflow'; print('OK')"`

## ロールバック確認対象

- 本タスクの変更は additive のみであり、既存 enum 値を削除・変更しないこと。
- ruff check が clean であること。

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
