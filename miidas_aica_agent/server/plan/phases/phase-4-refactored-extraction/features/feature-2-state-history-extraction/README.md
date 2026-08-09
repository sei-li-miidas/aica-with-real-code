# フィーチャー: state/history extraction

## 目的

session state と履歴 mapping を `chat_service_refactored.ChatService` から分離する。

## 親フェーズ

- フェーズ: phase-4-refactored-extraction

## スコープ

スコープ内:
- `ConversationState`
- `HistoryMapper`
- REST history stateless path
- history mapping real-refactored evidence

スコープ外:
- DB write side effects
- stream event loop

## 依存関係

- feature-1-refactored-bootstrap

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-conversation-state | session state を component 化する。 | bootstrap | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di` | not-started |
| task-2-history-mapper | history mapping を component 化する。 | task-1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di` | not-started |

## 完了条件

- REST history path が init 済み state に依存しない。
- history mapping scenario の real-refactored evidence が更新されている。
