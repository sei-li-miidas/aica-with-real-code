# フェーズ: endpoint/config 境界の固定

## 目的

Gate A の最初に、endpoint と config の shared boundary を固定し、後続の legacy/refactored 切替と rollback の前提を作る。

## スコープ

スコープ内:
- `agent_runtime.service_variant` と `agent_runtime.agent_model` の追加
- config 読み取り helper と startup validation
- `ChatServiceProtocol` の追加
- `endpoints.py` の concrete `chat_service` import と model hardcode の排除
- Phase 1 最小 contract harness
- Gate A pytest marker 登録
- `tests/integration/chat_service_contract/` の最小 scaffolding

スコープ外:
- `chat_service_refactored.py` の追加
- `service_variant: refactored` の valid 化
- Completions style / `api_style`

## 開始条件

- `server/plan/refactoring_plan.md` と `server/plan/architecture.md` が最新である。
- default config が現行 production chat behavior contract と互換であることを fixture-backed assertion で固定する方針が合意済みである。

## 終了条件

- `endpoints.py` が `services.chat_service` に依存しない。
- invalid config が app startup で fail fast する。
- `service_variant: refactored` は implementation 未登録として clear error になる。
- default config の chat model 解決は固定 model 名への暗黙依存ではなく、現行 production chat behavior contract との互換 fixture で検証されている。
- `server/pyproject.toml` に Gate A pytest marker が登録され、`tests/integration/chat_service_contract/` の最小 scaffolding が存在する。
- `server/plan/phases/gate_a_scenario_matrix.md` の startup config failure / default config compatibility / endpoint protocol boundary scenario が更新されている。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config` が pass、または marker 未作成時は task に列挙した exact fallback command がすべて pass している。

## フィーチャー

| フィーチャー | 目的 | 依存関係 | ステータス |
| --- | --- | --- | --- |
| feature-1-agent-runtime-config-endpoint-contract | endpoint/config 境界と最小 contract を固定する。 | owner/branch 割当 | done |

## 必須検証

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config`
- marker 未作成時は task に列挙した exact fallback command
- `server/plan/phases/gate_a_scenario_matrix.md` の該当 scenario evidence 更新
- `server/pyproject.toml` の pytest marker 登録
- `tests/integration/chat_service_contract/` の最小 scaffolding 存在確認

## メモ

- Phase 1 では `legacy` のみ valid にする。
