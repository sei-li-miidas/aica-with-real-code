# フィーチャー: history and DI

## 目的

DI コンテナ、履歴マッパー、turn 準備、persistence を completions style に対応させる。

## スコープ

スコープ内:
- `containers.py` の runner 切替
- `history_mapper.py` / `turn_preparer.py` / `chat_persistence.py` の completions 対応
- conversation retention と tool replay の保存・復元
- `replay_items` 契約への統一と replay/canonicalization 整合
- refactored service residual state access の `ConversationState` 直参照化

スコープ外:
- runner internal の細部検証
- parity / rollback test suite の最終化

## 開始条件

- feature-1-completions-foundation が完了している。
- `CompletionsAgentRunner` の contract が固定されている。

## 終了条件

- config に応じて runner が正しく注入される。
- completions history が既存 responses の保存形式を壊さない。
- turn preprocessing と persistence が style 非依存で動作する。

## フィーチャー内タスク

| タスク | 目的 | 依存関係 | ステータス |
| --- | --- | --- | --- |
| task-1-history-and-di | container wiring と history / persistence を completions 対応させる。 | feature-1-completions-foundation | done |
| task-2-replay-contract-and-state-access | replay 契約統一と refactored state access 整理を行う。 | task-1-history-and-di | done |
| task-3-anyllm-completions-provider | completions provider を LiteLLM から any-llm（chat_completions 固定・fallback flag 付き）へ移行し、依存を Python 3.14 対応へ入替える。 | task-2-replay-contract-and-state-access | done |

## 必須検証

- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_completions_history_and_di.py server/tests/integration/chat_service_contract/test_completions_history_and_di.py`
- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_llm_runner.py server/tests/unit/services/chat/test_stream_event_processor.py server/tests/unit/services/test_chat_service_refactored.py`
- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/test_runner_contract.py server/tests/integration/chat_service_contract/test_refactored_residual_coverage.py server/tests/integration/test_chat_subservice_residuals.py server/tests/integration/test_stream_event_processor_coverage.py`
- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract`

## メモ

- Gate B では runner 差分を `LLMRunner` に閉じ込め、上位サービスは style を意識しない。