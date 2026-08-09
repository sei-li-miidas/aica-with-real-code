# フィーチャー: stream/tool/security/workflow

## 目的

stream processing、tool handling、security cleanup、workflow/jobtype preprocessing を分離し、legacy dependency removal を完了する。

## 親フェーズ

- フェーズ: phase-4-refactored-extraction

## スコープ

スコープ内:
- `StreamEventProcessor`
- `ToolEventHandler`
- `StreamGuard`
- `WorkflowChatHandler`
- legacy dependency removal

スコープ外:
- Gate B runtime switching
- summary model switching

## 依存関係

- feature-3-persistence-turn-preparation

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-stream-event-processor | stream event loop と response yield を分離する。 | persistence/turn | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | done |
| task-2-tool-event-handler | tool call/output と tool response shape を分離する。 | task-1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | done |
| task-3-stream-guard-security | security detection と cancellation cleanup を分離する。 | task-2 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` | done |
| task-4-workflow-chat-handler | workflow/jobtype preprocessing を分離する。 | task-3 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` | done |
| task-5-legacy-dependency-removal | legacy dependency の再導入防止を固定する。 | task-4 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | done |

## 完了条件

- critical scenario がすべて `pass` である。
- `chat_service_refactored.py` は legacy `ChatService` へ import / instantiate / delegate しない。
