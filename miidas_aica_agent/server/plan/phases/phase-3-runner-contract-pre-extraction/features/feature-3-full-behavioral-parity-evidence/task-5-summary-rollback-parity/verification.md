# 検証: task-5-summary-rollback-parity

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `pytest -q server/tests/integration/chat_service_contract/test_summary_rollback.py` | pass | 4 passed, 2 skipped |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` | pass | 4 passed, 2 skipped |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | pass | 47 passed, 25 skipped |

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
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m rollback_summary` | pass | 4 passed, 2 skipped, 333 deselected (real-refactored pending-phase-4) |

## カバレッジ計測（feature-3 全タスク完了後）

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` | pass | 47 passed, 25 skipped; `services.chat_service` branch coverage 54% |

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity` | pass | 47 passed, 25 skipped |
| rollback_summary | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m rollback_summary` | pass | 4 passed, 2 skipped |

## 失敗したテスト

なし。

## 未実行

なし。

## 免除

なし。

## 未達ブランチ（カバレッジ計測後に記録）

| ブランチ | 分類 | 理由 | オーナー | フォローアップ |
| --- | --- | --- | --- | --- |
| residual reachable branches in `services.chat_service` | task-6 inventory | required scenario 完了後も branch coverage 54% のため | task-6 owner | task-6-coverage-gap-inventory で branch ごとに inventory 化する |

## 手動確認

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/integration/chat_service_contract/test_summary_rollback.py -q`: pass, 4 passed, 2 skipped。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/integration/chat_service_contract/test_summary_rollback.py -q --cov=services.chat_service --cov-branch --cov-report=term-missing`: pass, 4 passed, 2 skipped; `services.chat_service` branch coverage 11%。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing`: pass, 47 passed, 25 skipped; `services.chat_service` branch coverage 54%。
- `gate_a_scenario_matrix.md` の `summary rollback` の `legacy/delegating evidence` を `pass: pytest -q -m rollback_summary` に更新済み。
- `handoff.md` 更新済み。
- `status.md` 更新済み。

## レビュー / 修正ログ

| pass | reviewer | 結果 | 指摘 | 修正 | 再検証 |
| --- | --- | --- | --- | --- | --- |
| 1 | `code-reviewer` subagent | clean | blocking な指摘なし。direct negative assertion を足すとさらに堅くなる、という任意提案のみ | 追加修正なし | clean review 確認済み |
