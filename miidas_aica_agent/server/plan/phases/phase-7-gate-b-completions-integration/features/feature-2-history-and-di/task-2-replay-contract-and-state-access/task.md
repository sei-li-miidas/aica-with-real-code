# タスク: replay contract and state-access cleanup

## 目的

`LLMRunStream` の replay 契約を `replay_items` に統一し、refactored service の内部 state アクセスを `ConversationState` 直参照へ整理する。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズ README: `server/plan/phases/phase-7-gate-b-completions-integration/README.md`
- 親フィーチャー README: `server/plan/phases/phase-7-gate-b-completions-integration/features/feature-2-history-and-di/README.md`

## スコープ

許可する変更:
- `server/src/aica_agent/services/chat/llm_runner.py`
- `server/src/aica_agent/services/chat/stream_event_processor.py`
- `server/src/aica_agent/services/chat/tool_event_handler.py`
- `server/src/aica_agent/services/chat/history_mapper.py`
- `server/src/aica_agent/services/chat_service_refactored.py`
- replay/state-access 契約に関する unit / integration tests と fixture

許可しない変更:
- endpoint public response contract の変更
- DI container の追加責務導入
- parity / rollback suite の final gate 判定

## 依存関係

- task-1-history-and-di

## 実装メモ

- `tool_replay_items` は `replay_items` に置き換え、Responses/Completions の両経路で同一の読み口に統一する。
- Completions replay は function_call と function_call_output の整合を保つ最小 canonicalization を行う。
- `ChatService` 本体で stop-at-tool replay を扱う際は、`ToolEventHandler` が未初期化なら安全側で append をスキップする。
- refactored residual tests は backcompat property ではなく `ConversationState` 直参照 (`_state(...)`) で検証する。