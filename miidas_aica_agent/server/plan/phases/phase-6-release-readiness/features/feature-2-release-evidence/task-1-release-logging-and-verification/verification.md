# 検証: task-1-release-logging-and-verification

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| startup log evidence 確認 | pass | FastAPI lifespan が `startup runtime config: service_variant=... agent_model=... summary_model=... backend=responses` を logger から出すことを unit test で確認。 |
| chat turn log evidence 確認 | pass | `handle_chat_session()` / `process_chat_messages()` が `chat turn runtime: service_variant=... agent_model=... backend=responses chat_service=... request_type=...` を logger から出すことを endpoint contract test で確認。 |
| runtime logging focused tests | pass | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/unit/services/chat/test_agent_runtime_config.py server/tests/unit/test_application_runtime_logging.py server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py server/tests/integration/chat_service_contract/test_di_lifecycle.py` -> `34 passed in 0.24s` |
| release candidate verification checklist | pass | 必須 7 コマンドを `server/tests/` スコープで再実行し全件 pass。 |

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

## 必須確認

- startup log evidence 確認
- chat turn log evidence 確認
- release candidate verification checklist 作成
- `server/plan/phases/gate_a_scenario_matrix.md` の rollback subset matrix 完了確認

## release candidate verification checklist

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config server/tests/` | pass | `4 passed, 1491 deselected in 1.31s` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/` | pass | `30 passed, 1465 deselected in 1.78s` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/` | pass | `25 passed, 1470 deselected in 1.58s` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security server/tests/` | pass | `29 passed, 1466 deselected in 1.95s` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/` | pass | `14 passed, 1481 deselected in 1.54s` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap server/tests/` | pass | `8 passed, 1487 deselected in 1.39s` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/` | pass | `1196 passed, 299 deselected in 5.51s` |

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_endpoint_config | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config server/tests/` | pass | `4 passed, 1491 deselected` |
| rollback_di | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/` | pass | `30 passed, 1465 deselected` |
| rollback_runner | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/` | pass | `25 passed, 1470 deselected` |
| rollback_security | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security server/tests/` | pass | `29 passed, 1466 deselected` |
| rollback_summary | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/` | pass | `14 passed, 1481 deselected` |
| pre_extraction_bootstrap | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap server/tests/` | pass | `8 passed, 1487 deselected` |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/` | pass | `1196 passed, 299 deselected` |

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

- staging rollback drill の実施結果: not-applicable。
  - オーナー: sei.li@miidas.jp
  - 日付: 2026-06-09
  - 理由: feature-1 task-1 と同じく staging または同等環境への設定配布/rollout 権限がなく、drill は実施不可。
  - 代替確認: RC verification checklist（必須 7 marker command）は `server/tests/` scope で全件 pass（本 verification.md の release candidate verification checklist 参照）。技術的互換性 evidence は feature-1 task-1 で確立済み。
  - 実運用 drill の追跡先: Gate B の release candidate 承認ゲートで、staging rollback drill（実測時間・確認ログ・実施者）を必須確認として記録すること。
  - Gate A release candidate 承認への影響: Gate B は別 planning / evidence cycle であり、本 Gate A RC は技術的互換性 evidence と RC checklist pass で完成している。staging drill は Gate B entry 条件として切り離す。

- runtime logging evidence command (workspace root):
  - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/unit/services/chat/test_agent_runtime_config.py server/tests/unit/test_application_runtime_logging.py server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py server/tests/integration/chat_service_contract/test_di_lifecycle.py`
  - 結果: `34 passed in 0.24s`
- startup runtime log format:
  - `startup runtime config: service_variant=%s agent_model=%s summary_model=%s backend=%s`
  - `application.lifespan()` が `validate_agent_runtime_config(container.config)` 後に実アプリ logger から出力する。
- chat turn runtime log format:
  - `chat turn runtime: service_variant=%s agent_model=%s backend=%s chat_service=%s request_type=%s`
  - 初回 START は `handle_chat_session()`、通常メッセージは `process_chat_messages()` が実 endpoint logger から出力する。

## RC 判定ルール適用

- Phase 6 README ルールにより、required marker command は `server/tests/` スコープで全件 pass。
- 本 task のステータスは `done` とする。
