# 検証: boundary foundation

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config` (cwd: workspace root) | pass | 4 passed。 |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/test_restful_api_endpoints.py server/tests/unit/test_websocket_endpoint.py` | not-applicable | marker が作成済みのため fallback は不要。 |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_agent_runtime_config.py server/tests/unit/services/chat/test_config_validator.py` (cwd: workspace root) | pass | 7 passed。 |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py` (cwd: workspace root) | pass | 4 passed。 |
| `server/pyproject.toml` Gate A marker 登録確認 | pass | `[tool.pytest.ini_options]` に Gate A markers を登録済み。 |
| `server/tests/integration/chat_service_contract/` scaffolding 存在確認 | pass | `server/tests/integration/chat_service_contract/fixtures/` を追加済み。 |

結果値:
- `pass`
- `fail`
- `not-run`
- `waived`
- `not-applicable`

## 必須コマンド

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config` (cwd: workspace root)
- marker 未作成時のみ、以下をすべて実行する。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/test_restful_api_endpoints.py server/tests/unit/test_websocket_endpoint.py` (cwd: workspace root)
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_agent_runtime_config.py server/tests/unit/services/chat/test_config_validator.py` (cwd: workspace root)
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py` (cwd: workspace root)
- `server/pyproject.toml` Gate A marker 登録確認
- `server/tests/integration/chat_service_contract/` scaffolding 存在確認
- default config と現行 production chat behavior contract の互換 fixture assertion 確認

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_endpoint_config | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config` (cwd: workspace root) | pass | 4 passed。 |
| rollback_endpoint_config | fallback commands listed above | not-applicable | marker 作成済みのため fallback 不要。 |
| marker registration | `server/pyproject.toml` Gate A marker 登録確認 | pass | marker を pyproject に追加済み。 |
| contract scaffold | `server/tests/integration/chat_service_contract/` scaffolding 存在確認 | pass | `fixtures/` を追加済み。 |

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

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_agent_runtime_config.py server/tests/unit/services/chat/test_config_validator.py`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py`
