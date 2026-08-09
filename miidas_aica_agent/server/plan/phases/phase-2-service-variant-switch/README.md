# フェーズ: service variant 切替口の追加

## 目的

legacy と refactored の `ChatService` を並行存在させ、config だけで DI 解決を切り替えられる状態にする。

## スコープ

スコープ内:
- `Container.chat_svc` の factory lifecycle 保護
- 一時 delegating adapter としての `chat_service_refactored.ChatService`
- `service_variant: refactored` の valid 化
- legacy/refactored 共通 fixture による wiring parity

スコープ外:
- 独立した refactored 実装の parity 証明
- main `chat()` path の legacy 委譲削除

## 開始条件

- Phase 1 が完了している。
- endpoint は `ChatServiceProtocol` に依存している。

## 終了条件

- `chat_service.py` と `chat_service_refactored.py` が同時に import できる。
- `agent_runtime.service_variant` により legacy/refactored を切り替えられる。
- `Container.chat_svc()` が singleton ではないことがテストで保証されている。
- `server/plan/phases/gate_a_scenario_matrix.md` の DI lifecycle scenario が更新されている。

## フィーチャー

| フィーチャー | 目的 | 依存関係 | ステータス |
| --- | --- | --- | --- |
| feature-1-di-lifecycle-baseline | legacy 設定での factory lifecycle を固定する。 | Phase 1 | done |
| feature-2-delegating-adapter-service-switch | refactored delegating adapter と切替を追加する。 | feature-1 | not-started |

## 必須検証

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`
- `server/plan/phases/gate_a_scenario_matrix.md` の DI lifecycle evidence 更新

## メモ

- Phase 2 の refactored pass は wiring parity であり、独立実装の parity ではない。
