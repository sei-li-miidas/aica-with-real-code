# タスク: delegating adapter service switch

## 目的

一時 delegating adapter と service variant switch を追加し、`service_variant: refactored` を選択可能にする。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズREADME: `server/plan/phases/phase-2-service-variant-switch/README.md`
- 親フィーチャーREADME: `server/plan/phases/phase-2-service-variant-switch/features/feature-2-delegating-adapter-service-switch/README.md`
- 依存タスクの引き継ぎ: `server/plan/phases/phase-2-service-variant-switch/features/feature-1-di-lifecycle-baseline/task-1-di-lifecycle-baseline/handoff.md`

## スコープ

許可する変更:
- `server/src/aica_agent/services/chat_service_refactored.py`
- `server/src/aica_agent/containers.py`
- `server/src/aica_agent/services/chat/config_validator.py`
- legacy/refactored 共通 contract harness
- service variant switch tests
- `server/plan/phases/gate_a_scenario_matrix.md` の DI lifecycle delegating evidence

許可しない変更:
- refactored main `chat()` path の独立実装
- Gate B 設定
- legacy から refactored への依存追加

## 依存関係

- DI lifecycle baseline

## 実装メモ

- Phase 2 の refactored は legacy へ委譲してよい一時 adapter とする。
- contract pass は wiring / endpoint boundary / response shape の確認として扱う。

## 必須テスト

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`
- `server/plan/phases/gate_a_scenario_matrix.md` の DI lifecycle delegating evidence 更新

## ロールバック確認対象

- 必須サブセット: `rollback_di`
- 必須コマンド: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`

## 完了条件

- legacy/refactored が config で切り替えられる。
- delegating adapter が独立 parity 証明ではないことを `handoff.md` に明記する。
- `gate_a_scenario_matrix.md` の delegating evidence は wiring evidence として記録され、final parity evidence として扱わないことが明記されている。
- `handoff.md`、`verification.md`、`server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- delegating adapter の削除予定と削除条件を残す。
