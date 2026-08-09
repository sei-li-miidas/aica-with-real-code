# 検証: task-2-legacy-delegating-characterization

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/integration/chat_service_contract -q -m pre_extraction_parity --tb=short` (cwd: workspace root) | pass | `40 passed, 17 skipped, 14 deselected`。legacy/delegating characterization を実行し、real-refactored は `pending-phase-4` として skip。 |

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

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/integration/chat_service_contract -q -m pre_extraction_parity --tb=short` (cwd: workspace root)

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/integration/chat_service_contract -q -m pre_extraction_parity --tb=short` (cwd: workspace root) | pass | legacy/delegating characterization は pass。real-refactored は Phase 4 owner が `pending-phase-4` を埋める。 |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| 該当なし | なし | なし |

## 未実行

| コマンド | 理由 |
| --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` | この task の必須コマンドは `pre_extraction_parity`。rollback subset は該当 owner task で実行。 |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` | この task の必須コマンドは `pre_extraction_parity`。rollback subset は該当 owner task で実行。 |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` | この task の必須コマンドは `pre_extraction_parity`。rollback subset は該当 owner task で実行。 |

## 免除

| コマンド | オーナー | 理由 | 日付 | フォローアップ |
| --- | --- | --- | --- | --- |
| 該当なし | - | - | - | - |

## 手動確認

- `server/plan/phases/gate_a_scenario_matrix.md` の Phase 3 owner 分シナリオで `legacy evidence` / `delegating evidence` を更新し、`real-refactored evidence` は `pending-phase-4` を維持した。

