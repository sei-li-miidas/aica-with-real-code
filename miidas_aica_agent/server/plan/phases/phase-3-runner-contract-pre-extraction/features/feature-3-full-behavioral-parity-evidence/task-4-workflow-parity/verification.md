# 検証: task-4-workflow-parity

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `pytest -q server/tests/integration/chat_service_contract/test_workflow_side_effects.py` | pass | 8 passed, 4 skipped |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | pass | 47 passed, 25 skipped |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` | pass | 14 passed, 7 skipped |

結果値:
- `pass`
- `fail`
- `not-run`
- `waived`
- `not-applicable`

完了ルール:
- 必須コマンドに `fail` または `not-run` がある間は、タスクを `done` にできない。
- `waived` は、免除セクションにオーナー、理由、日付、フォローアップがある場合のみ許可する。
- `not-applicable` は、理由がある場合のみ許可する。

## 必須コマンド

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity` | pass | 47 passed, 25 skipped, 267 deselected (real-refactored pending-phase-4) |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m rollback_security` | pass | 14 passed, 7 skipped, 318 deselected (real-refactored pending-phase-4) |

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity` | pass | 47 passed, 25 skipped |
| rollback_security | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m rollback_security` | pass | 14 passed, 7 skipped |

## 失敗したテスト

なし。

## 未実行

なし。

## 免除

なし。

## 手動確認

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/integration/chat_service_contract/test_workflow_side_effects.py -q`: pass, 8 passed, 4 skipped。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/integration/chat_service_contract/test_workflow_side_effects.py -q --cov=services.chat_service --cov-branch --cov-report=term-missing`: pass, 8 passed, 4 skipped; `services.chat_service` branch coverage 31%。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing`: pass, 47 passed, 25 skipped; `services.chat_service` branch coverage 52%。
- `gate_a_scenario_matrix.md` の `workflow side effects` の `legacy evidence` を `pass: pytest -q -m pre_extraction_parity` に更新済み。
- `handoff.md` 更新済み。
- `status.md` 更新済み。

## レビュー / 修正ログ

| pass | reviewer | 結果 | 指摘 | 修正 | 再検証 |
| --- | --- | --- | --- | --- | --- |
| 1 | `code-reviewer` subagent | request-changes | stream contract helper が全 response を見ていない、workflow submitted が persisted role を見ていない、matrix/status/task docs 未更新 | `_assert_stream_contract()` を強化、`saved_history_pairs` を追加、不要 fixture field を削除、matrix/status/handoff/verification を更新 | `test_workflow_side_effects.py`, `pre_extraction_parity`, `rollback_security` を再実行して pass |
| 2 | `code-reviewer` subagent | clean | changed test/fixture files に追加指摘なし | 追加修正なし | clean review 確認済み |
