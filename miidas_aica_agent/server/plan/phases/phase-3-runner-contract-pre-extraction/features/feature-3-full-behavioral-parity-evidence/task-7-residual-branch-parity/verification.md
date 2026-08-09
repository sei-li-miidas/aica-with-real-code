# 検証: task-7-residual-branch-parity

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `python3 -m py_compile server/src/aica_agent/services/chat_service.py` | pass | revert 後の構文確認。 |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/test_chat_entrypoint_guards.py server/tests/integration/chat_service_contract/test_init_session_residuals.py server/tests/integration/chat_service_contract/test_previous_history_contract.py server/tests/integration/chat_service_contract/test_runner_residual_branches.py server/tests/integration/chat_service_contract/test_security_cleanup.py server/tests/integration/chat_service_contract/test_workflow_side_effects.py` | pass | `106 passed, 44 skipped` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` | waived | command 自体は成功し、tests は `161 passed, 73 skipped, 267 deselected`。user 指示で legacy stream-loop change を採用しないため、coverage は `99%`、残差 `661->978` を waiver として記録する。 |

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

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing`

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| `pre_extraction_parity` full coverage | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` | waived | `161 passed, 73 skipped, 267 deselected`、`Stmts 787 / Miss 0 / Branch 348 / BrPart 1 / Coverage 99%`。残差は `661->978` (`async for event in run_result.stream_events()` の zero-yield fallthrough) |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| なし | tests は pass している。coverage 100% 未達は下記の免除として記録する。 | - |

## 未実行

| コマンド | 理由 |
| --- | --- |
| なし | - |

## 免除

| コマンド | オーナー | 理由 | 日付 | フォローアップ |
| --- | --- | --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` | user / task owner | user 指示で legacy `async for event in run_result.stream_events()` の explicit async iterator 化を採用しないため。tests は `161 passed, 73 skipped, 267 deselected` で pass し、未達は coverage 上の `661->978` のみ。 | 2026-05-25 | Phase 4 の real-refactored evidence で再確認する。legacy loop rewrite を許容する判断が出た場合のみ、この waiver を外して 100% closure を再実施する。 |

## 手動確認

- `real-refactored` evidence は task scope 外のため今回も skip のまま。Phase 4 で再開する。
- `661->978` は behavioral test で空 stream の完了を確認していても、coverage tool は legacy `async for` の暗黙終端を branch として credit しない。
