# フェーズ: Gate B completions integration

## 目的

Gate A の構造リファクタ完了後に、Completions style runtime switching と non-OpenAI provider onboarding を追加し、rollback safety を config-only で保証する。

## スコープ

スコープ内:
- `agent_runtime.api_style` の追加と validity matrix の固定
- `legacy + completions` の startup/config validation failure
- `refactored + completions` の runner / container / persistence 対応
- `CompletionsAgentRunner` / `CompletionsRunStream`
- `completions_contract` / `completions_runner_internal` / `rollback_api_style` の検証

スコープ外:
- summary path の provider onboarding
- endpoints.py の public response contract 変更
- Gate A の legacy/refactored parity 仕様の再定義

## 開始条件

- Gate A が完了している。
- `service_variant: legacy` / `service_variant: refactored` の切替が config-only で成立している。
- Responses style の contract harness と rollback subset が利用可能である。

## 終了条件

- `legacy + completions` が startup/config validation で明示的に拒否される。
- `refactored + completions` が observable parity suite を pass する。
- completions runner internal invariants が pass する。
- rollback が config-only で成立し、smoke で確認済みである。
- summary path が runtime switching の影響を受けないことを確認済みである。

## フィーチャー

| フィーチャー | 目的 | 依存関係 | ステータス |
| --- | --- | --- | --- |
| feature-1-completions-foundation | config / model / runner の completions 基盤を作る。 | なし | not-started |
| feature-2-history-and-di | DI / history / persistence を completions 対応させる。 | feature-1-completions-foundation | not-started |
| feature-3-parity-and-rollback | parity / rollback / verification suite を固定する。 | feature-2-history-and-di | done |

## 必須検証

- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_runner_internal server/tests/`
- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract server/tests/`
- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_api_style server/tests/`

## メモ

- Gate B は `api_style` を追加する最初の段階であり、Gate A の legacy/refactored boundary を壊さないことを前提にする。