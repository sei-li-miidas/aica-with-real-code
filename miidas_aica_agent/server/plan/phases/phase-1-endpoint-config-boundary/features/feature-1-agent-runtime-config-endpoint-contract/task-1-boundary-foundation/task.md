# タスク: boundary foundation

## 目的

`agent_runtime` config、startup validation、endpoint decoupling、`ChatServiceProtocol`、Phase 1 最小 contract harness を追加する。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズREADME: `server/plan/phases/phase-1-endpoint-config-boundary/README.md`
- 親フィーチャーREADME: `server/plan/phases/phase-1-endpoint-config-boundary/features/feature-1-agent-runtime-config-endpoint-contract/README.md`
- 依存タスクの引き継ぎ: なし

## スコープ

許可する変更:
- `server/src/aica_agent/endpoints.py`
- `server/src/aica_agent/application.py`
- `server/src/aica_agent/config.yml`
- `server/src/aica_agent/services/chat/service_protocol.py`
- `server/src/aica_agent/services/chat/agent_runtime_config.py`
- `server/src/aica_agent/services/chat/config_validator.py`
- `server/src/aica_agent/services/chat_service.py` の `init_session()` 引数名整理
- `server/pyproject.toml` の pytest marker 登録
- `server/tests/integration/chat_service_contract/` の最小 scaffolding
- Phase 1 に必要な unit / contract tests
- `server/plan/phases/gate_a_scenario_matrix.md` の startup config failure / default config compatibility / endpoint protocol boundary evidence

許可しない変更:
- `chat_service_refactored.py` の追加
- `service_variant: refactored` の valid 化
- `api_style` / Completions style の追加
- summary model 設定の変更

## 依存関係

- なし

## 実装メモ

- pytest command は `server` を current working directory として実行する。
- `agent_runtime.agent_model` は `model_list.use_for: agent` に存在する必要がある。
- default config は固定 model 名ではなく、現行 production chat behavior contract と互換であることを fixture-backed assertion で検証する。
- 現行 model 名は reference fixture の期待値として記録してよいが、Gate A の durable invariant にはしない。
- `endpoints.py` からの `init_session()` 呼び出しは positional call のまま維持する。
- invalid config は module import 時ではなく app startup で fail させる。
- `server/pyproject.toml` の Gate A marker 登録は、この task の最初に行う。test file 作成や marker command 実行より前に登録し、以降の task が marker 名を参照できる状態にする。
- `server/pyproject.toml` に下記 marker を登録する。
  - `rollback_endpoint_config`
  - `rollback_di`
  - `rollback_runner`
  - `rollback_security`
  - `rollback_summary`
  - `pre_extraction_bootstrap`
  - `pre_extraction_parity`
- 下記 fallback test file は Phase 1 の明示的な task output として作成する。既存 file がなければ、この task で追加する。
  - `server/tests/unit/services/chat/test_agent_runtime_config.py`
  - `server/tests/unit/services/chat/test_config_validator.py`
  - `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py`
- `server/tests/integration/chat_service_contract/fixtures/` は Phase 1 で最小構造を作り、startup config failure / default config compatibility / endpoint protocol boundary fixture を置く。

## 必須テスト

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config`
- marker 未作成の場合に限り、下記の exact fallback command をすべて実行して `verification.md` に記録する。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/test_restful_api_endpoints.py server/tests/unit/test_websocket_endpoint.py`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_agent_runtime_config.py server/tests/unit/services/chat/test_config_validator.py`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py`
- `server/plan/phases/gate_a_scenario_matrix.md` の startup config failure / default config compatibility / endpoint protocol boundary evidence 更新

## ロールバック確認対象

- 必須サブセット: `rollback_endpoint_config`
- 必須コマンド: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config`
- marker 未作成時の exact fallback command:
  - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/test_restful_api_endpoints.py server/tests/unit/test_websocket_endpoint.py`
  - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_agent_runtime_config.py server/tests/unit/services/chat/test_config_validator.py`
  - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py`

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`、または `pass` 以外の各コマンドに文書化された免除がある。
- `gate_a_scenario_matrix.md` の startup config failure / default config compatibility / endpoint protocol boundary evidence が `pass`、`waived`、または理由付き `not-applicable` である。
- `server/pyproject.toml` に Gate A markers が登録されている。
- Phase 1 fallback test file が存在し、marker command または fallback command で実行されている。
- `tests/integration/chat_service_contract/` の最小 scaffolding が存在し、Phase 3 が fixture / marker membership を追加できる。
- 各免除に、オーナー、理由、日付、フォローアップが含まれている。
- 必須ロールバック確認対象が `pass`、または理由付きで明示的に `not-applicable` と記録されている。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
