# フィーチャー: parity and rollback

## 目的

observable parity と rollback safety を integration test で固定する。

## スコープ

スコープ内:
- `completions_contract` integration suite
- `rollback_api_style` smoke suite
- startup / runtime / rollback の evidence 記録

スコープ外:
- 低レベルな runner 実装変更
- DI / history / persistence の機能追加

## 開始条件

- feature-2-history-and-di が完了している。
- completions runner が実行可能である。

## 終了条件

- `refactored + responses` と `refactored + completions` の observable parity が pass する。
- `api_style: completions -> responses` の rollback が config-only で成立する。
- `service_variant: refactored -> legacy` の rollback も成立する。

## フィーチャー内タスク

| タスク | 目的 | 依存関係 | ステータス |
| --- | --- | --- | --- |
| task-1-parity-and-rollback | parity / rollback の統合テストを追加する。 | feature-2-history-and-di | done |

## 必須検証

- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract server/tests/`
- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_api_style server/tests/`

## RC threshold recording

- Gate B promotion thresholds は task-1 parity-and-rollback の verification に記録する。
- threshold の target / owner / due / evidence を埋めてから RC 判定に進む。
- evidence には dashboard link か runbook path を含める。

## メモ

- Gate B の rollback は自動 failover ではなく config rollback を前提にする。