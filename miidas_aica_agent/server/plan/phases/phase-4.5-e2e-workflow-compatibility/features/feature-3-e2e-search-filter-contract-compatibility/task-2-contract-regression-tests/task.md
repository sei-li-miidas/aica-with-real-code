# タスク: task-2-contract-regression-tests

## 目的

親 feature README の task table で定義された成果を実装する。詳細 scope は親 feature README と親 phase README を source of truth とする。

## 最初に読むコンテキスト

- 親フェーズ README: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/README.md`
- 親フィーチャー README: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/features/feature-3-e2e-search-filter-contract-compatibility/README.md`
- 依存タスクの引き継ぎ: `server/plan/phases/phase-4.5-e2e-workflow-compatibility/features/feature-3-e2e-search-filter-contract-compatibility/task-1-other-filter-type-compatibility/handoff.md`
- 変更対象ファイル:
  - `e2e/tests/client/test_workflow_contract_validation.py`（新規）
  - `e2e/tests/client/test_workflow_receive_dispatch_send_compatibility.py`（新規）
  - 必要最小限の test support file（新規）

## スコープ

許可する変更:
- `e2e/tests/client/` 配下に focused compatibility test を追加する。
- テスト追加に必要な最小限の fixture/support コードを `e2e/tests/` 配下へ追加する。

許可しない変更:
- サーバー側ファイル
- workflow runtime ロジック本体の追加変更（必要なら別タスク）
- broad test architecture の再設計

## 変更対象

| ファイル | 変更内容 |
| --- | --- |
| `e2e/tests/client/test_workflow_contract_validation.py` | workflow payload validation / contract failure を固定するテストを追加する。 |
| `e2e/tests/client/test_workflow_receive_dispatch_send_compatibility.py` | receive -> pending -> dispatch -> send の互換性回帰を固定するテストを追加する。 |

## 依存関係

- feature-3 task-1-other-filter-type-compatibility

## 実装メモ

- 本 phase の source of truth（`phase-4.5` README、feature-3 README、task-1 の blocker/handoff）で定義された validation/test 方針に従う。
- drift が再発した場合に failure reason が分かる assertion message を付ける。
- 既存 e2e 実行パスを壊さないよう、テストは mocked exchange/payload 中心にする。

## 必須テスト

- `cd e2e && ../.venv-e2e/bin/python -m ruff check src/`
- `cd e2e && ../.venv-e2e/bin/python -m pytest -q tests/client/test_workflow_contract_validation.py tests/client/test_workflow_receive_dispatch_send_compatibility.py`

## ロールバック確認対象

- 新規テストが drift を検知できること（意図した failure がテストで明確化されること）。
- 追加テストが既存の workflow 非発火シナリオ前提を壊さないこと。

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。