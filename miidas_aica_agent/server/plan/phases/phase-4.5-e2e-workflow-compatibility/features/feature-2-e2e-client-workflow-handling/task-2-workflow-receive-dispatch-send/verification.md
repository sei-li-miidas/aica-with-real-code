# 検証: task-2-workflow-receive-dispatch-send

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `cd e2e && ../.venv-e2e/bin/python -m ruff check src/` | pass | 指示に従い `.venv-server` 同等コマンド `cd e2e && ../.venv-server/bin/python -m ruff check src/` で実行し `All checks passed!` を確認。 |
| workflow 発火シナリオ e2e 実行（手動） | fail | `.venv-server` で `cd e2e && set -a && source .env.local && set +a && ../.venv-server/bin/python src/aica_client/main.py --run-mode TEST` を実行。`rest_format_invalid: source=positions/search_filter/current, details=other filter Type must be single|multiple, actual ... 'Type': 'multi_select'` で workflow 到達前に停止。 |
| 非発火シナリオ回帰確認（手動） | fail | `FINISH_POLICY=EITHER MAX_ROUNDS=1` を付与して同コマンドを再実行したが、同一 `rest_format_invalid` で初期化段階で停止。 |

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

- `cd e2e && ../.venv-e2e/bin/python -m ruff check src/`
- workflow 発火シナリオ e2e 実行（手動）: `./e2e/start_test.sh`（local server 必須）
- 非発火シナリオ回帰確認（手動）

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| regression check | `cd e2e && set -a && source .env.local && set +a && FINISH_POLICY=EITHER MAX_ROUNDS=1 ../.venv-server/bin/python src/aica_client/main.py --run-mode TEST` | fail | workflow に入る前の `positions/search_filter/current` contract mismatch で停止。jobtype/position dispatch 回帰の実行確認はブロック。 |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| `cd e2e && set -a && source .env.local && set +a && ../.venv-server/bin/python src/aica_client/main.py --run-mode TEST` | `rest_format_invalid` (`other filter Type must be single|multiple`, actual=`multi_select`) により workflow 受信前に停止。 | `positions/search_filter/current` のレスポンス形式を e2e contract に合わせるか、e2e 側許容型を別タスクで拡張してから再実行。 |
| `cd e2e && set -a && source .env.local && set +a && FINISH_POLICY=EITHER MAX_ROUNDS=1 ../.venv-server/bin/python src/aica_client/main.py --run-mode TEST` | 同上。非発火シナリオでも同一初期化エラーで停止。 | 同上。 |

## 未実行

| コマンド | 理由 |
| --- | --- |
| `./e2e/start_test.sh` | Critical instruction により Python 実行は `.venv-server` を使用する必要があるため、等価コマンドへ置換して実行。 |

## 免除

| コマンド | オーナー | 理由 | 日付 | フォローアップ |
| --- | --- | --- | --- | --- |
| なし | - | - | - | - |

## 手動確認

- `/tmp/e2e_client/persona_definition_01_bedrock-claude-v1_20260607144558950_6dd176605c10476da2fd46c88431ef7f.log` を確認。
- `workflow_received` / `workflow_submitting` / `workflow_handled` は未出力（workflow 到達前に `rest_format_invalid` で停止）。
- blocker 解消後に workflow 発火シナリオを再実行して `workflow_handled` を再確認する必要あり。
