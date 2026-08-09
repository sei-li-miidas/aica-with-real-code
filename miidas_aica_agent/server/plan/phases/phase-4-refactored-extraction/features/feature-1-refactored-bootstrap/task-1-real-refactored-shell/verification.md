# 検証: task-1-real-refactored-shell

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/test_chat_service_refactored.py` (cwd: workspace root) | pass | `32 passed` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q --cov=services.chat_service_refactored --cov-branch --cov-fail-under=100 server/tests/unit/services/test_chat_service_refactored.py` (cwd: workspace root) | pass | `32 passed`、`services.chat_service_refactored` branch coverage `100.00%` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/test_refactored_bootstrap_shell.py` (cwd: workspace root) | pass | `1 passed` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/test_di_lifecycle.py` (cwd: workspace root) | pass | `7 passed` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap` (cwd: workspace root) | pass | `4 passed, 3 skipped, 520 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` (cwd: workspace root) | pass | parity regression check。`162 passed, 73 skipped, 292 deselected` |

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

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap` (cwd: workspace root)
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q --cov=services.chat_service_refactored --cov-branch --cov-fail-under=100 server/tests/unit/services/test_chat_service_refactored.py` (cwd: workspace root)
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` (cwd: workspace root)

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| `pre_extraction_bootstrap` | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap` (cwd: workspace root) | pass | `runner event normalization` / `stop-at-tool replay` / `usage propagation` の real-refactored evidence を更新。 |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| なし | - | - |

## 未実行

| コマンド | 理由 |
| --- | --- |
| なし | - |

## 免除

| コマンド | オーナー | 理由 | 日付 | フォローアップ |
| --- | --- | --- | --- | --- |
| なし | - | - | - | - |

## 手動確認

- `pre_extraction_bootstrap` の skip 3 件は `task-2-bootstrap-behavioral-proof` が担当する `legacy dependency reintroduction` behavioral proof placeholder。task-1 scope 外のため継続して skip。
- `delegating-refactored` characterization は `chat_service_contract` fixture の `_delegate_chat=True` compatibility mode で維持され、`pre_extraction_parity` regression check が pass することを確認した。
- follow-up hardening として、DI wiring、stream cleanup、cancellation propagation、session logging context cleanup を focused regression で再確認した。
