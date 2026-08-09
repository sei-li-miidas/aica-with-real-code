# 検証: task-3-test-migration-map

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/ -m pre_extraction_parity` | pass | 37 passed, 20 skipped (real-refactored pending-phase-4), 0 failed |
| `server/plan/phases/gate_a_scenario_matrix.md` の該当 evidence 確認 | not-applicable | 本 task は migration map の作成が scope（documentation のみ）。scenario evidence 自体は task-2 で更新済み。task-3 はその evidence を参照して migration map 内に記録するだけであり、evidence 更新自体は実施しない。 |

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

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/ -m pre_extraction_parity`

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| `pre_extraction_parity` | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/ -m pre_extraction_parity` | pass | 37 passed, 20 skipped (real-refactored), 0 failed |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| (なし) | — | — |

## 未実行

| コマンド | 理由 |
| --- | --- |
| (なし) | — |

## 免除

| コマンド | オーナー | 理由 | 日付 | フォローアップ |
| --- | --- | --- | --- | --- |
| (なし) | — | — | — | — |

## 手動確認

