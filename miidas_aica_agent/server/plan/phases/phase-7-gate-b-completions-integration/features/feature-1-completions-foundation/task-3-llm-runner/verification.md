# 検証: completions llm runner

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_runner_internal server/tests/` | pass | 5 passed, 1532 deselected |

## 必須コマンド

- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_runner_internal`

## 確認観点

- `CompletionsRunStream.continuation_state` が runner-local state container を返し、`run_state` を next turn の input に渡せること。
- `replay_items` に stop-at-tool / function call output が含まれ、次 turn の input replay に使えること。
- handoff / retry state が continuation container に閉じ込められ、Responses contract と分離されること。
- `CompletionsAgentRunner` が `run_config` を保持し、`Runner.run_streamed(..., run_config=...)` に渡すこと。

## 未実行

| コマンド | 理由 |
| --- | --- |
| なし | 必須コマンドを実行して pass した |