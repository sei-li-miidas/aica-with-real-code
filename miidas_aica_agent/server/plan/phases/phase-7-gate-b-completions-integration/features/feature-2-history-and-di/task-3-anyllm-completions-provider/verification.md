# 検証: anyllm completions provider migration

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_completions_history_and_di.py server/tests/integration/chat_service_contract/test_completions_history_and_di.py` | pass | `9 passed in 0.10s` |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_llm_runner.py server/tests/unit/services/chat/test_stream_event_processor.py server/tests/unit/services/test_chat_service_refactored.py` | pass | `160 passed in 3.01s` |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract server/tests/` | pass | `11 passed, 1569 deselected in 1.35s` |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit`（litellm uninstall 後の全 unit） | pass | `956 passed`（any-llm 既定・litellm 不在で成立） |

## 必須コマンド

- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_completions_history_and_di.py server/tests/integration/chat_service_contract/test_completions_history_and_di.py`
- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/chat/test_llm_runner.py server/tests/unit/services/chat/test_stream_event_processor.py server/tests/unit/services/test_chat_service_refactored.py`
- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract server/tests/`

## 対象テスト

- `server/tests/unit/services/chat/test_llm_runner.py`
- `server/tests/unit/services/chat/test_stream_event_processor.py`
- `server/tests/unit/services/test_chat_service_refactored.py`
- `server/tests/unit/services/chat/test_completions_history_and_di.py`
- `server/tests/integration/chat_service_contract/test_completions_history_and_di.py`

## 記入必須の観点

- 既定 completions provider が `AnyLLMProvider` であり、`AICA_COMPLETIONS_PROVIDER=litellm` で従来経路へ fallback する。
- any-llm provider が `api="chat_completions"` で生成され、Responses API 経路を選ばない。
- 不正な `AICA_COMPLETIONS_PROVIDER` 値が `ValueError` になる。
- `aiohttp` が first-party 依存として patched 版で明示宣言され、LiteLLM 除去後も import が成立する。
- lock から `litellm` / 脆弱 `aiohttp` が除去され、CVE 対象パッケージが patched 版へ bump されている。

### 観測結果

- `_build_completions_model_provider()` は env 既定で `AnyLLMProvider` を返し、`litellm` 指定で
  `LitellmProvider`、不正値で `ValueError` を返すことを test で確認した。
- `_build_anyllm_model_provider()` が `api == "chat_completions"` の `AnyLLMProvider` を返し、
  `get_model("openai/...")._selected_api()` が `chat_completions` を選ぶことを確認した。
- litellm を venv から uninstall した状態でも全 unit（956 passed）が成立し、既定経路が any-llm のみで動くことを確認した。
- 再 lock 後 `requirements.txt` に `litellm` / `aiohttp==3.13.5` が存在せず、`aiohttp==3.14.1`・
  `python-dotenv==1.2.2`・`python-multipart==0.0.32`・`starlette==1.3.1`・`any-llm-sdk==1.17.0`・
  `anthropic`(any-llm-sdk core 依存) が含まれることを確認した。Bedrock の `boto3`/`botocore` は
  `[bedrock]` extra 未導入のため含まれない。

### 失敗時の rollback 参照

- `server/tests/integration/chat_service_contract/test_runner_contract.py`
- `server/tests/unit/services/chat/test_llm_runner.py::test_completions_runner_builds_anyllm_run_config_by_default`

## 未実行

| コマンド | 理由 |
| --- | --- |
| 実 Bedrock / Claude 疎通 | 現行は OpenAI のみ使用し Bedrock/Claude 依存（`[bedrock]` extra 等）も未導入のため本タスク範囲外。採用時に feature-3 等で実施。 |
| `pre-commit run pip-audit`（hook 経由） | ローカル環境の ensurepip 不具合で hook の sub-venv 生成が失敗。lock 内容の grep と venv audit で代替確認済み。 |
