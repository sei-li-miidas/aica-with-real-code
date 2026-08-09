# 検証: task-2-tool-result-parity

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | pass | 45 passed, 24 skipped |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` | pass | 26 passed, 10 skipped |

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

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` (cwd: workspace root) | pass | 45 passed, 24 skipped (real-refactored pending-phase-4) |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` (cwd: workspace root) | pass | 26 passed, 10 skipped (real-refactored pending-phase-4) |

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` (cwd: workspace root) | pass | 45 passed, 24 skipped |
| rollback_runner | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` (cwd: workspace root) | pass | 26 passed, 10 skipped |

## 失敗したテスト

なし。

## 未実行

なし。

## 免除

なし。

## 手動確認

- `gate_a_scenario_matrix.md` の `tool result response shape` の `legacy evidence` を `fixture-schema only` → `pass: pytest -q -m pre_extraction_parity` に更新済み。
- `handoff.md` 更新済み。
- `status.md` 更新済み。

