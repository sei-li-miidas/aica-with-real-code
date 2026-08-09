# タスク: anyllm completions provider migration

## 目的

completions runner の model provider を LiteLLM から any-llm に切り替える。Python 3.14 で
install できず脆弱な transitive 依存を固定する LiteLLM を既定から外し、Python 3.14 対応の
any-llm を既定 provider とする。LiteLLM は feature flag で選べる fallback として残す。
現行 config の利用 provider は OpenAI（`openai/gpt-4.1`）。Bedrock / Claude は any-llm が
対応する将来オプションであり、本タスクでは有効化しない。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズ README: `server/plan/phases/phase-7-gate-b-completions-integration/README.md`
- 親フィーチャー README: `server/plan/phases/phase-7-gate-b-completions-integration/features/feature-2-history-and-di/README.md`

## 背景

- LiteLLM は Python 3.14 を `1.83.7` までしか支えず、その版は `aiohttp==3.13.5` /
  `python-dotenv==1.0.1` を脆弱バージョンに固定する（pip-audit で 21 件検出）。
- 1.83.8 以降は `requires-python <3.14` のため、本プロジェクトの Python 3.14 制約下では bump できない。
- any-llm は Python 3.14 対応で、OpenAI Agents SDK に `AnyLLMProvider` が同梱される。現行は
  OpenAI のみ使用する。Bedrock（`[bedrock]` extra の boto3/SigV4）や Claude（`anthropic` SDK の
  ネイティブ Messages API）は any-llm が対応する将来オプションで、本タスクの依存には含めない。

## スコープ

許可する変更:
- `server/src/aica_agent/services/chat/llm_runner.py`（provider builder と feature flag）
- `server/pyproject.toml`（core 依存・optional extra の入替）
- `server/requirements.txt` / `server/requirements-dev.txt`（再 lock）
- `server/tests/unit/services/chat/test_llm_runner.py`（provider 選択・API 固定の test）

許可しない変更:
- endpoint public response contract の変更
- DI container の追加責務導入（provider 選択は runner 内に閉じる）
- config schema (`agent_runtime.api_style` 等) の意味変更
- parity / rollback suite の final gate 判定

## 依存関係

- task-2-replay-contract-and-state-access

## 実装メモ

- `AICA_COMPLETIONS_PROVIDER` env で provider を切替える。既定 `anyllm`、`litellm` 指定で従来経路に fallback。
  不正値は `ValueError`。
- any-llm provider は `AnyLLMProvider(api="chat_completions")` で生成する。`api=None` だと
  `AnyLLMModel._selected_api()` が provider 次第で Responses API を選び、Agents SDK 内部の
  Responses 形式履歴（assistant の `output_text` item）が Responses **input** schema 検証で弾かれる。
  `CompletionsAgentRunner` は Chat Completions style 用なので、LiteLLM と同じく chat_completions に固定する。
- `aiohttp` は `api_repo` / `maintenance_manager` / `utils.http` が直接使う first-party 依存だが、
  従来は LiteLLM 経由の間接依存だった。LiteLLM を外すと import が壊れるため、patched 版
  (`~=3.14.1`) を core 依存として明示宣言する。
- pyproject では `any-llm-sdk` を core に、`litellm` を optional extra に移す。`anthropic` /
  `openai` は any-llm-sdk の core 依存なので extra 指定は不要（`anthropic` は lock に入るが現行未使用）。
  Bedrock を使う場合のみ `[bedrock]` extra（boto3）を追加するが、本タスクでは導入しない。
- 再 lock で `python-dotenv` / `python-multipart` / `starlette` を patched 版へ bump し、pip-audit の指摘を解消する。
