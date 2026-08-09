# 検証: replay contract and state-access cleanup

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_llm_runner.py server/tests/unit/services/chat/test_stream_event_processor.py server/tests/unit/services/test_chat_service_refactored.py` | pass | `144 passed in 3.73s` |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/test_runner_contract.py server/tests/integration/chat_service_contract/test_refactored_residual_coverage.py server/tests/integration/test_chat_subservice_residuals.py server/tests/integration/test_stream_event_processor_coverage.py` | pass | `102 passed in 0.30s` |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract server/tests/` | pass | `11 passed, 1550 deselected in 1.46s` |

## 必須コマンド

- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_llm_runner.py server/tests/unit/services/chat/test_stream_event_processor.py server/tests/unit/services/test_chat_service_refactored.py`
- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/test_runner_contract.py server/tests/integration/chat_service_contract/test_refactored_residual_coverage.py server/tests/integration/test_chat_subservice_residuals.py server/tests/integration/test_stream_event_processor_coverage.py`
- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract server/tests/`

## 対象テスト

- `server/tests/unit/services/chat/test_llm_runner.py`
- `server/tests/unit/services/chat/test_stream_event_processor.py`
- `server/tests/unit/services/test_chat_service_refactored.py`
- `server/tests/integration/chat_service_contract/test_runner_contract.py`
- `server/tests/integration/chat_service_contract/test_refactored_residual_coverage.py`
- `server/tests/integration/test_chat_subservice_residuals.py`
- `server/tests/integration/test_stream_event_processor_coverage.py`

## 記入必須の観点

- replay 契約統一（`tool_replay_items` -> `replay_items`）が Responses/Completions 双方で成立している。
- Completions replay canonicalization が function_call/function_call_output の整合性を維持する。
- refactored residual tests が `ConversationState` 直参照に移行し、backcompat property 依存を除去している。
- stop-at-tool replay append が ToolEventHandler 非初期化時に安全側でスキップされる。

### 観測結果

- `LLMRunStream` protocol と関連 test fixture を `replay_items` へ統一し、stream processor/runner contract 参照の naming drift を解消した。
- `CompletionsRunStream` は replay items を保持しつつ、fake id 正規化と replay canonicalization を追加し、次 turn 入力整合を強化した。
- `chat_service_refactored.py` は stop-at-tool output append で `ToolEventHandler` 非初期化時の unsafe fallback を廃止し、error log を出して noop する。
- residual integration tests は `_state(...)` helper を介した `ConversationState` 検証へ移行し、backcompat setter/property に依存しない前提へ揃えた。

### 失敗時の rollback 参照

- `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py::test_startup_validation_rejects_legacy_completions_api_style`
- `server/tests/integration/chat_service_contract/test_runner_contract.py::test_responses_run_stream_normalizes_sdk_shaped_events`

## 未実行

| コマンド | 理由 |
| --- | --- |
| なし | 必須コマンドを実行して pass した |