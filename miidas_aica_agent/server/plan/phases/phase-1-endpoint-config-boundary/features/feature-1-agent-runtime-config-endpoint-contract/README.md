# フィーチャー: agent runtime config と endpoint contract

## 目的

endpoint/config 境界を固定し、legacy 実装の外部挙動を保ったまま後続の service variant switch を可能にする。

## 親フェーズ

- フェーズ: phase-1-endpoint-config-boundary

## スコープ

スコープ内:
- `agent_runtime.service_variant` / `agent_runtime.agent_model`
- `agent_runtime_config.py`
- `config_validator.py`
- `application.py` startup validation
- `ChatServiceProtocol`
- `endpoints.py` の import decoupling と model config 化
- legacy の最小 contract harness
- Gate A pytest marker 登録
- `server/tests/integration/chat_service_contract/` の最小 scaffolding
- default config と現行 production chat behavior contract の互換 fixture assertion

スコープ外:
- `chat_service_refactored.py`
- `service_variant: refactored` の valid 化
- Completions style

## 依存関係

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-boundary-foundation | endpoint/config 境界を実装し最小 contract を追加する。 | owner/branch 割当 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config` | done |

## 完了条件

- default config が現行 production chat behavior contract と互換であることを fixture-backed assertion で確認している。
- default config の検証は特定の固定 model 名への暗黙依存を gate にしない。
- `endpoints.py` が `services.chat_service` を import しない。
- `service_variant: refactored` は clear startup/config validation error になる。
- `gate_a_scenario_matrix.md` の startup config failure / default config compatibility / endpoint protocol boundary scenario が更新されている。
- `server/pyproject.toml` に Gate A pytest markers が登録されている。
- `server/tests/integration/chat_service_contract/` の最小 scaffolding と Phase 1 fallback test file が存在する。

## メモ

- `init_session()` は positional call を維持する。
