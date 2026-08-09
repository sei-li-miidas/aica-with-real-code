# タスク: task-1-other-filter-type-compatibility

## 目的

親 feature README の task table で定義された成果を実装する。詳細 scope は親 feature README と親 phase README を source of truth とする。

## 最初に読むコンテキスト

- 親フェーズ README: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/README.md`
- 親フィーチャー README: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/features/feature-3-e2e-search-filter-contract-compatibility/README.md`
- blocker 記録: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/features/feature-2-e2e-client-workflow-handling/task-2-workflow-receive-dispatch-send/verification.md`
- 変更対象ファイル: `e2e/src/aica_client/client/e2e_client.py`

## スコープ

許可する変更:
- `e2e/src/aica_client/client/e2e_client.py` の search filter 正規化処理に対する additive / minimal targeted change のみ。

このタスクではテスト実装を必須にしない。回帰固定テストの追加は feature-3 の task-2 で実施する。

許可しない変更:
- workflow enum / request type / pending workflow state の変更
- workflow dispatch ロジックの変更
- サーバー側のファイル

## 変更対象

| ファイル | 変更内容 |
| --- | --- |
| `e2e/src/aica_client/client/e2e_client.py` | `positions/search_filter/current` の `OtherFilters[].Type` が既存値以外でも、既知差分を正規化または許容して `rest_format_invalid` で停止しないようにする。 |

## 依存関係

- feature-2 task-2 の verification で `positions/search_filter/current` blocker が記録されていること

## 実装メモ

- source of truth は feature-2 task-2 verification に記録された blocker 内容と実ランタイムの payload shape とする。
- additive change とし、既存の `single|multiple` 受理を壊さない。
- server の payload drift を吸収する task であり、workflow ロジックへ手を広げない。

## 必須テスト

- `cd e2e && ../.venv-e2e/bin/python -m ruff check src/`
- `cd e2e && set -a && source .env.local && set +a && ../.venv-e2e/bin/python src/aica_client/main.py --run-mode TEST` を用いた search filter current refresh の手動確認
- feature-2 task-2 の workflow 発火 / 非発火確認を再実行

## ロールバック確認対象

- 既存の search filter contract (`single|multiple`) を引き続き受理すること。
- workflow path に入る前の初期化経路のみを unblock し、他の pending action dispatch を変えないこと。

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
- task-2-contract-regression-tests へ、再現 payload と期待挙動を引き継ぐ。