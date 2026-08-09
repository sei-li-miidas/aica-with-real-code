# タスク: DI lifecycle baseline

## 目的

`service_variant: legacy` での `Container.chat_svc` 解決と instance lifecycle を固定する。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズREADME: `server/plan/phases/phase-2-service-variant-switch/README.md`
- 親フィーチャーREADME: `server/plan/phases/phase-2-service-variant-switch/features/feature-1-di-lifecycle-baseline/README.md`
- 依存タスクの引き継ぎ: `server/plan/phases/phase-1-endpoint-config-boundary/features/feature-1-agent-runtime-config-endpoint-contract/task-1-boundary-foundation/handoff.md`

## スコープ

許可する変更:
- `server/src/aica_agent/containers.py`
- DI lifecycle unit tests
- WebSocket/session instance lifecycle tests
- REST history stateless path tests
- `server/plan/phases/gate_a_scenario_matrix.md` の DI lifecycle legacy evidence

許可しない変更:
- `chat_service_refactored.py` の追加
- `service_variant: refactored` の valid 化
- `Container.chat_svc` の singleton 化

## 依存関係

- boundary foundation

## 実装メモ

- この task では legacy provider の lifecycle を保護するだけに留める。
- `refactored` variant は次 task で implementation 登録と同時に valid 化する。

## 必須テスト

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`
- `server/plan/phases/gate_a_scenario_matrix.md` の DI lifecycle legacy evidence 更新

## ロールバック確認対象

- 必須サブセット: `rollback_di`
- 必須コマンド: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`、または `pass` 以外の各コマンドに文書化された免除がある。
- `gate_a_scenario_matrix.md` の DI lifecycle legacy evidence が更新されている。
- `handoff.md`、`verification.md`、`server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- legacy provider の lifecycle に関する前提を `handoff.md` に残す。
