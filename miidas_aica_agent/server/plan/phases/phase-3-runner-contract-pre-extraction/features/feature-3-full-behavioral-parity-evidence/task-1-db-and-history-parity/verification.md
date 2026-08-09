# 検証: task-1-db-and-history-parity

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/integration/chat_service_contract/test_history_mapping.py server/tests/integration/chat_service_contract/test_db_side_effects.py -v` | pass | 18 passed, 9 skipped (real-refactored は Phase 4 待ち) |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity` | pass | 43 passed, 23 skipped (ベースラインと同数) |

完了ルール:
- 必須コマンドに `fail` または `not-run` がある間は、タスクを `done` にできない。
- `waived` は、免除セクションにオーナー、理由、日付、フォローアップがある場合のみ許可する。
- `not-applicable` は、理由がある場合のみ許可する。

## 必須コマンド

実行済みコマンド:

```
cd <repo_root>
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest \
  server/tests/integration/chat_service_contract/test_history_mapping.py \
  server/tests/integration/chat_service_contract/test_db_side_effects.py -v
```

```
cd <repo_root>
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest \
  server/tests/ -q -m pre_extraction_parity
```

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/` | pass | 43 passed, 23 skipped |
| rollback_di | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/` | pass | history mapping tests included |
| rollback_runner | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/` | pass | db side effects tests included |

## 失敗したテスト

なし。

## 未実行

| コマンド | 理由 |
| --- | --- |
| `real-refactored` variant の各テスト | Phase 4 bootstrap 完了後に skip 解除予定 |

## 免除

なし。

## 手動確認
