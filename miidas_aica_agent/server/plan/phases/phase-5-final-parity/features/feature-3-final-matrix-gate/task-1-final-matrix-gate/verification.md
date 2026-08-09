# 検証: task-1-final-matrix-gate

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/` | pass | `1183 passed, 299 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config server/tests/` | pass | `4 passed, 1478 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/` | pass | `30 passed, 1452 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/` | pass | `25 passed, 1457 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security server/tests/` | pass | `29 passed, 1453 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/` | pass | `14 passed, 1468 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ --cov=services.chat_service --cov-branch --cov-report=term-missing` | pass | `1183 passed, 299 deselected` / `chat_service.py` branch `99%`（missing `667->976`） |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ --cov=services.chat_service_refactored --cov-branch --cov-report=term-missing` | pass | `1183 passed, 299 deselected` / `chat_service_refactored.py` branch `98%`（missing `67->69`, `71->73`, `761->804`, `827-829`, `836`） |

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

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ --cov=services.chat_service --cov-branch --cov-report=term-missing`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ --cov=services.chat_service_refactored --cov-branch --cov-report=term-missing`

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_endpoint_config | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config server/tests/` | pass | `4 passed, 1478 deselected` |
| rollback_di | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/` | pass | `30 passed, 1452 deselected` |
| rollback_runner | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/` | pass | `25 passed, 1457 deselected` |
| rollback_security | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security server/tests/` | pass | `29 passed, 1453 deselected` |
| rollback_summary | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/` | pass | `14 passed, 1468 deselected` |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/` | pass | `1183 passed, 299 deselected` |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| なし | なし | なし |

## 未実行

| コマンド | 理由 |
| --- | --- |
| なし | なし |

## 免除

| コマンド | オーナー | 理由 | 日付 | フォローアップ |
| --- | --- | --- | --- | --- |
| なし | なし | なし | なし | なし |

## 手動確認

- `server/plan/phases/gate_a_scenario_matrix.md` の required scenario matrix を更新し、`startup config failure` / `default config compatibility` / `endpoint protocol boundary` / `DI lifecycle` の `real-refactored evidence` を `pass` へ更新した。
- critical scenario（DB side effects / tool result response shape / security block cleanup / cancellation cleanup / legacy dependency reintroduction）に `waived` / `not-applicable` / `not-run` / `fail` がないことを確認した。
- final matrix gate 判定を `pass` とし、Phase 5 の release 判定に必要な final evidence を固定した。

