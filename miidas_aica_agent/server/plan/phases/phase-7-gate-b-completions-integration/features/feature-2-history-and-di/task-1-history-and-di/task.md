# タスク: history and DI wiring

## 目的

DI container と history / persistence の completions 対応を入れる。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズ README: `server/plan/phases/phase-7-gate-b-completions-integration/README.md`
- 親フィーチャー README: `server/plan/phases/phase-7-gate-b-completions-integration/features/feature-2-history-and-di/README.md`

## スコープ

許可する変更:
- `server/src/aica_agent/containers.py`
- `server/src/aica_agent/services/chat/chat_persistence.py`
- `server/src/aica_agent/services/chat/history_mapper.py`
- `server/src/aica_agent/services/chat/turn_preparer.py`
- style-aware integration tests

許可しない変更:
- runner internal state mapping の再設計
- parity / rollback suite の final 化

## 依存関係

- feature-1-completions-foundation

## 実装メモ

- style の差分は `LLMRunner` に閉じ込める。
- persistence / mapping / turn preparation は style 非依存に寄せる。