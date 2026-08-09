# タスク: completions llm runner

## 目的

`CompletionsRunStream` と `CompletionsAgentRunner` を実装する。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズ README: `server/plan/phases/phase-7-gate-b-completions-integration/README.md`
- 親フィーチャー README: `server/plan/phases/phase-7-gate-b-completions-integration/features/feature-1-completions-foundation/README.md`

## スコープ

許可する変更:
- `server/src/aica_agent/services/chat/llm_runner.py`
- `LiteLLM` adapter の接続と、既存の依存解決ポイントへの最小限の登録（`llm_runner.py` が直接必要とする範囲のみ）
- `server/pyproject.toml`
- `server/requirements.txt`
- `completions_runner_internal` tests

許可しない変更:
- DI コンテナの全面的な wiring / factory 差し替え
- history / persistence / rollback suite

## 依存関係

- task-1-schema-and-matrix

## 実装メモ

- continuation state, tool replay, handoff / retry state を completions 側に閉じ込める。
- Responses style の stable contract は壊さない。
- non-OpenAI provider の実呼び出しは LiteLLM 経由の provider 実行経路を使う。
- `verified` の判定は adapter 経由の疎通に加えて、tool calling / structured outputs / usage reporting が `completions_runner_internal` と staging / canary の検証で確認済みであることを前提にする。