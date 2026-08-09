# 検証: schema and validity matrix

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_agent_runtime_config.py server/tests/unit/services/chat/test_config_validator.py server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py` | pass | 42 passed |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract server/tests/` | pass | 2 passed, 1530 deselected |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_api_style server/tests/` | pass | 2 passed, 1530 deselected |

## 必須コマンド

- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_agent_runtime_config.py server/tests/unit/services/chat/test_config_validator.py server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py`
- `server/pyproject.toml` の marker 登録確認
- `server/src/aica_agent/config.yml` の validity matrix 確認

## 確認観点

- `api_style` 未指定時の default が `responses` であることを確認済み。
- `api_style: responses` の明示設定が default と同じ結果になることを確認済み。
- `legacy + completions` が startup/config validation で fail fast することを確認済み。
- `refactored + completions` が startup/config validation で accepted されることを確認済み。

## 未実行

| コマンド | 理由 |
| --- | --- |
| なし | 必須コマンドはすべて実行済み |