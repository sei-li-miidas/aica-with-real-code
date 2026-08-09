# 検証: history and DI wiring

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_completions_history_and_di.py server/tests/integration/chat_service_contract/test_completions_history_and_di.py` | pass | `8 passed in 0.08s` |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract server/tests/` | pass | `10 passed, 1534 deselected in 1.57s` |

## 必須コマンド

- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_completions_history_and_di.py server/tests/integration/chat_service_contract/test_completions_history_and_di.py`
- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract server/tests/`

## 対象テスト

- `server/tests/unit/services/chat/test_completions_history_and_di.py`
- `server/tests/integration/chat_service_contract/test_completions_history_and_di.py`
- `server/tests/unit/services/chat/test_config_validator.py`
- `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py`

## 記入必須の観点

- completions-aware DI wiring の実証結果
- history / persistence が completions 経路で壊れていないことの比較結果
- 失敗時に参照する rollback 手順リンク

### 観測結果

- `containers.py` の `refactored_llm_runner` は `agent_runtime.api_style` に応じて `ResponsesAgentRunner` と `CompletionsAgentRunner` を切り替える。
- `HistoryMapper` / `TurnPreparer` / `ChatPersistence` の生成・型は api_style に依存せず同一であることを integration test で確認した。
- completions style で利用される tool output wrapper（`{"text": "...json..."}`）を `HistoryMapper.parse_tool_output` が処理できることを unit test で確認した。
- `ChatPersistence` の tool output serialization は style 非依存で JSON 互換を維持することを unit test で確認した。

### 失敗時の rollback 参照

- `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py::test_startup_validation_rejects_legacy_completions_api_style`
- `server/tests/unit/services/chat/test_config_validator.py::test_validate_agent_runtime_config_rejects_legacy_with_completions`

## 未実行

| コマンド | 理由 |
| --- | --- |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract` | workspace root から実行すると `cli/tests` も収集され `commands` import 解決に失敗するため、Gate B server scope の `server/tests/` を付与して実行した。 |