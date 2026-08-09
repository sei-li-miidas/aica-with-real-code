# 検証: task-1-final-contract-suite

## テスト概要

実行メタ情報:
- 実行者: `sei.li@miidas.jp`
- 実行ブランチ: `feature/77996_chat_service_refactoring_phase_5_feature_1_task_1`

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` (cwd: workspace root) | pass | `153 passed, 8 skipped, 668 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` (cwd: workspace root) | pass | `12 passed, 817 deselected` |

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

実行ディレクトリ前提:
- workspace root (`miidas_aica_agent/`) で実行する。

```bash
# pre_extraction_parity (cwd: workspace root)
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity

# rollback_summary (cwd: workspace root)
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary
```

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | pass | `153 passed, 8 skipped, 668 deselected` |
| rollback_summary | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` | pass | `12 passed, 817 deselected` |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| `.venv-server/bin/python -m pytest -q -m pre_extraction_parity` (cwd: workspace root) | `PYTHONPATH` 未設定のため import error (`ModuleNotFoundError`) で collection fail。 | 同じ cwd (workspace root) のまま `PYTHONPATH=server/src/aica_agent` を付与して再実行し pass。 |

## 未実行

なし。

## 免除

なし。

## 手動確認

なし。

