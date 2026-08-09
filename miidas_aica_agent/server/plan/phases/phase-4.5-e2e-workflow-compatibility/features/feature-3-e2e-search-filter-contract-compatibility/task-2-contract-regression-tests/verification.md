# 検証: task-2-contract-regression-tests

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `cd e2e && ../.venv-server/bin/python -m ruff check src/` | pass | task 指示に従い `.venv-e2e` 指定を `.venv-server` に置換して実行。出力: `All checks passed!` |
| `cd e2e && ../.venv-server/bin/python -m pytest -q tests/client/test_workflow_contract_validation.py tests/client/test_workflow_receive_dispatch_send_compatibility.py` | not-run | `e2e/tests/` ディレクトリがリポジトリに存在しないため pytest 収集不可。テストファイルを PR に含める必要がある。 |

結果値:
- `pass`
- `fail`
- `not-run`
- `waived`
- `not-applicable`

完了ルール:
- 必須コマンドに `fail` または `not-run` がある間は、タスクを `done` にできない。
- `waived` は、免除セクションにオーナー、理由、日付、フォローアップがある場合のみ許可する。
- `not-applicable` は、理由がある場合のみ許可する。

## 必須コマンド

- `cd e2e && ../.venv-server/bin/python -m ruff check src/`（`.venv-e2e` から `.venv-server` へ置換）
- `cd e2e && ../.venv-server/bin/python -m pytest -q tests/client/test_workflow_contract_validation.py tests/client/test_workflow_receive_dispatch_send_compatibility.py`（`.venv-e2e` から `.venv-server` へ置換）

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| focused compatibility tests | `cd e2e && ../.venv-server/bin/python -m pytest -q tests/client/test_workflow_contract_validation.py tests/client/test_workflow_receive_dispatch_send_compatibility.py` | not-run | テストファイルが `e2e/tests/` に存在しないため未実行。 |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| なし | - | - |

## 未実行

| コマンド | 理由 |
| --- | --- |
| `cd e2e && ../.venv-server/bin/python -m pytest -q tests/client/test_workflow_contract_validation.py tests/client/test_workflow_receive_dispatch_send_compatibility.py` | `e2e/tests/` ディレクトリおよびテストファイルがリポジトリに存在しない。テストファイルを追加してから再実行する必要がある。 |

## 免除

| コマンド | オーナー | 理由 | 日付 | フォローアップ |
| --- | --- | --- | --- | --- |
| なし | - | - | - | - |

## 手動確認

- テストファイルをリポジトリに追加後、`pytest -q` 11 passed を確認してから `done` に変更する。
