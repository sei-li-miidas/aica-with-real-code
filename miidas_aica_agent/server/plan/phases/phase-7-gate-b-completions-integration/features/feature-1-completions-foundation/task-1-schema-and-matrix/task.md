# タスク: schema and validity matrix

## 目的

`agent_runtime.api_style` の config schema と runtime validity matrix を追加する。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズ README: `server/plan/phases/phase-7-gate-b-completions-integration/README.md`
- 親フィーチャー README: `server/plan/phases/phase-7-gate-b-completions-integration/features/feature-1-completions-foundation/README.md`

## スコープ

許可する変更:
- `server/src/aica_agent/config.yml`
- `server/src/aica_agent/services/chat/config_validator.py`
- `server/src/aica_agent/services/chat/agent_runtime_config.py`
- `server/pyproject.toml` の pytest marker 登録
- Gate B の最小 unit / integration tests

許可しない変更:
- `CompletionsAgentRunner` 実装
- history / persistence の completions 対応

## 依存関係

- なし

## 実装メモ

- `api_style` は `responses | completions` とする。
- `legacy + completions` は startup/config validation で fail fast にする。
- default は `responses` とする。
- `server/pyproject.toml` の Gate B marker 登録は、この task の最初に行う。test file 作成や marker command 実行より前に登録し、以降の task が marker 名を参照できる状態にする。登録対象は `completions_runner_internal`, `completions_contract`, `rollback_api_style`。