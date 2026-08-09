# 引き継ぎ: completions llm runner

## 概要

記入必須タイミング: task 実装完了後、Status を `done` にする前。

`CompletionsRunStream` と `CompletionsAgentRunner` を追加した。Responses style は既存 contract のまま維持し、completions 側は runner-local の continuation state を返すようにした。

レビューで弾く条件:
- 変更ファイル、互換性メモ、次タスクへのフォローアップ、未解決の質問のいずれかが `未記入` のまま。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat/llm_runner.py` | `CompletionsRunStream` / `CompletionsRunContinuationState` / `CompletionsAgentRunner` を追加した。Responses の replay helper も共通化した。 |
| `server/pyproject.toml` | `litellm~=1.83.7` を追加した。 |
| `server/requirements.txt` | `litellm==1.83.7` を追加した。 |
| `server/tests/unit/services/chat/test_llm_runner.py` | completions runner internal テストを追加した。 |

## 互換性メモ

- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_runner_internal server/tests/` は `5 passed, 1532 deselected` で pass した。
- Responses style の `ResponsesRunStream` / `ResponsesAgentRunner` contract は維持し、`continuation_state` と `tool_replay_items` の既存動作を壊していない。
- `CompletionsAgentRunner` は LiteLLM provider を lazy に構築するため、optional dependency が未導入でも unit tests は runner の contract 検証まで実行できる。

## 次タスクへのフォローアップ

- 次 task は `CompletionsRunContinuationState.run_state` を前提に completions 側の continuation / replay / retry を発展させてよい。
- 次 task は `tool_replay_items` を runner-local の replay payload として前提にできる。
- 追加の marker は不要。`completions_runner_internal` で runner-internal 契約を固定できる。

## 未解決の質問

- なし。LiteLLM の実 transport については後続 task / environment で検証する。