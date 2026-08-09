# フィーチャー: persistence/turn preparation

## 目的

DB write side effects と LLM turn input preparation を専用 component に分離する。

## 親フェーズ

- フェーズ: phase-4-refactored-extraction

## スコープ

スコープ内:
- `ChatPersistence`
- `TurnPreparer`
- DB side effects evidence
- position detail turn preparation

スコープ外:
- stream/tool dispatch
- security cleanup

## 依存関係

- feature-2-state-history-extraction

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-chat-persistence | session/history/tool output write を component 化する。 | state/history | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` | not-started |
| task-2-turn-preparer | turn input preparation を component 化する。 | task-1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` | not-started |

## 完了条件

- DB side effects critical scenario が `pass` である。
- `TurnPreparer` が stream event を処理しない。
