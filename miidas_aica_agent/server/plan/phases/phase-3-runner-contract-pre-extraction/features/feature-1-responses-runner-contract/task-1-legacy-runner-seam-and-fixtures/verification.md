# 検証: task-1-legacy-runner-seam-and-fixtures

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` | pass | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` を実行し、`4 passed, 264 deselected` だった。 |
| `server/plan/phases/gate_a_scenario_matrix.md` runner fixture evidence 更新 | pass | runner event normalization / stop-at-tool replay / usage propagation の legacy evidence を `tests/integration/chat_service_contract/test_runner_contract.py` に紐づけた。 |
| `tests/integration/chat_service_contract/fixtures/` scaffold 存在確認 | pass | `sdk_stream_events.py` / `stop_at_tool_replay.json` / `usage_response.json` を追加した。 |

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

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner`
- `server/plan/phases/gate_a_scenario_matrix.md` runner fixture evidence 更新
- `tests/integration/chat_service_contract/fixtures/` scaffold 存在確認

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_runner | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` | pass | 4 passed, 264 deselected。 |
| runner fixture evidence | `server/plan/phases/gate_a_scenario_matrix.md` runner fixture evidence 更新 | pass | runner contract scaffold を matrix に記録した。 |
| contract scaffold | `tests/integration/chat_service_contract/fixtures/` scaffold 存在確認 | pass | runner fixture を追加した。 |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| なし | なし | なし |

## 未実行

| コマンド | 理由 |
| --- | --- |
| なし | なし |

## 免除

| コマンド | オーナー | 理由 | 日付 | フォローアップ |
| --- | --- | --- | --- | --- |
| なし | なし | なし | なし | なし |

## 手動確認
