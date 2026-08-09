# 引き継ぎ: anyllm completions provider migration

## 概要

completions runner の既定 model provider を LiteLLM から any-llm へ移行した。`AICA_COMPLETIONS_PROVIDER`
env で provider を切替えられ、既定 `anyllm` / `litellm` 指定で従来経路に fallback する。any-llm は
`AnyLLMProvider(api="chat_completions")` で生成し、Responses API 経路に逸れて履歴 item が input schema
検証で弾かれる問題を防ぐ。依存も入替え、LiteLLM が固定していた脆弱な transitive 依存を解消した。

レビューで弾く条件:
- 変更ファイル、互換性メモ、次タスクへのフォローアップ、未解決の質問のいずれかが `未記入` のまま。
- provider 切替・API 固定・依存入替のいずれかが test で追跡できない。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat/llm_runner.py` | `_build_anyllm_model_provider()` と `_build_completions_model_provider()`（`AICA_COMPLETIONS_PROVIDER` 切替）を追加し、`CompletionsAgentRunner._get_run_config` を新 selector 経由に変更。any-llm は `api="chat_completions"` で固定。 |
| `server/pyproject.toml` | core 依存に `aiohttp~=3.14.1`(明示宣言) と `any-llm-sdk~=1.17.0` を追加、`litellm` は optional extra へ移動。 |
| `server/requirements.txt` | 再 lock。`litellm` / `aiohttp(3.13.5)` を除去、`aiohttp==3.14.1` を first-party として明示し、`any-llm-sdk` / `anthropic`(core 依存) を追加、CVE 対象を patched 版へ bump。 |
| `server/requirements-dev.txt` | 上記と同じ再 lock 結果（dev/test extra 付き）。 |
| `server/tests/unit/services/chat/test_llm_runner.py` | 既定 provider が `AnyLLMProvider`、any-llm が `api="chat_completions"`、flag dispatch / 不正値の test を追加・更新。 |

## 依存バージョン差分（lock）

| パッケージ | before | after | 備考 |
| --- | --- | --- | --- |
| litellm | 1.83.7 | （除去） | optional extra `litellm` 経由のみ |
| aiohttp | 3.13.5（litellm 経由の暗黙依存） | 3.14.1（first-party 明示） | 11 件の CVE 解消 |
| python-dotenv | 1.0.1 | 1.2.2 | CVE 解消 |
| python-multipart | 0.0.28 | 0.0.32 | CVE 解消 |
| starlette | 1.0.1 | 1.3.1 | CVE 解消 |
| any-llm-sdk | - | 1.17.0 | 新規 core 依存 |
| anthropic | - | 0.109.2 | any-llm-sdk の core 依存として lock に入る（現行 config では未使用） |
| openai | 1.x | 2.30.0 | openai-agents 0.13.6 が許容（major bump）。現行の唯一の利用 provider |

> Bedrock の `[bedrock]` extra（`boto3`）は本タスクでは導入しない。lock に `boto3`/`botocore` は含まれない。

## 互換性メモ

- 既定経路が LiteLLM → any-llm に変わるが、`CompletionsAgentRunner` の public contract は不変。
  provider 切替は runner 内に閉じ、上位サービス・DI container は変更しない。
- any-llm を `chat_completions` に固定したことで、LiteLLM 時と同じく Agents SDK の Responses 形式履歴を
  chat messages へ変換して送る。履歴の保存フォーマットには影響しない。
- `aiohttp` は元々 first-party で使われていた（`api_repo` / `maintenance_manager` / `utils.http`）が
  未宣言だった。今回 patched 版を明示宣言したことで、LiteLLM 除去後も import が成立する。
- `litellm` を使う場合は `AICA_COMPLETIONS_PROVIDER=litellm` を設定し、`pip install` 時に
  optional extra `litellm` を追加導入する必要がある（Python 3.14 では 1.83.7 が上限）。

## 次タスクへのフォローアップ

- 現行の利用 provider は OpenAI のみ。Bedrock / Claude を有効化する場合は別途対応が必要（以下は将来オプション）。
- Bedrock を使う場合は `[bedrock]` extra（boto3）を追加し re-lock した上で、model 文字列を LiteLLM 形式
  (`bedrock_converse:...`) から any-llm 形式 (`bedrock/anthropic.claude-...`) に remap する必要がある
  （`config.yml` / `e2e/config.yml` の `model_list`）。
- any-llm bedrock provider は sync boto3 を `loop.run_in_executor` で逃がす。Bedrock 採用時に高 WebSocket
  並行で使う場合は、既定 ThreadPoolExecutor サイズが上限になるため executor を tuning すること。
- openai 2.x への major bump は openai-agents 0.13.6 が宣言上許容し unit は通るが、responses 経路の
  runtime sanity を別途確認すること。
- 実 Bedrock / Claude 呼び出しの疎通確認は本タスク範囲外（依存も未導入）。採用時に feature-3 等で実施する。

## 未解決の質問

- なし。provider 切替・API 固定・依存入替は local diff 範囲で完了。実 provider 疎通は次フィーチャーで検証する。
