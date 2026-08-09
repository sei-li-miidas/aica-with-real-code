# 検証: task-1-other-filter-type-compatibility

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `cd e2e && ../.venv-e2e/bin/python -m ruff check src/` | pass | 指示に従い `.venv-server` 同等コマンド `cd e2e && ../.venv-server/bin/python -m ruff check src/` で実行。`All checks passed!` を確認。 |
| `cd e2e && set -a && source .env.local && set +a && ../.venv-e2e/bin/python src/aica_client/main.py --run-mode TEST` | fail | 指示に従い `.venv-server` 同等コマンド `cd e2e && set -a && source .env.local && set +a && ../.venv-server/bin/python src/aica_client/main.py --run-mode TEST` で再実行。`current_search_filter_loaded` と `jobtype_specific_search_validated` まで進み、旧 blocker（`multi_select` / `NoneType > int` / `Jobtypes must be object`）は解消。最終的に `apply/finish` が 400（`BasicInfo.email` 重複）で `finish_reason=apply_finish_failed`。 |
| feature-2 task-2 の workflow 発火 / 非発火確認再実行 | fail | 非発火相当コマンド `cd e2e && set -a && source .env.local && set +a && FINISH_POLICY=EITHER MAX_ROUNDS=1 ../.venv-server/bin/python src/aica_client/main.py --run-mode TEST` は `finish_reason=max_rounds` で完走。発火相当コマンドはサーバー混雑レスポンス（`大変混み合っております...`）が継続して workflow 発火ログ (`workflow_received`) まで到達した証跡を取れず、再確認が必要。 |

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
- `cd e2e && set -a && source .env.local && set +a && ../.venv-e2e/bin/python src/aica_client/main.py --run-mode TEST`
- feature-2 task-2 の workflow 発火 / 非発火確認再実行

実行補足:
- Critical execution rule により `.venv-e2e` 指定コマンドはすべて `.venv-server` 等価コマンドで実行した。

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| static check | `cd e2e && ../.venv-server/bin/python -m ruff check src/` | pass | `e2e_client.py` と `models.py` の互換修正後も lint pass。 |
| legacy `single|multiple` 受理維持 | `cd e2e && set -a && source .env.local && set +a && ../.venv-server/bin/python src/aica_client/main.py --run-mode TEST` | pass | `current_search_filter_loaded` / `jobtype_specific_search_validated` を確認し、`OtherFilters.Type=multi_select` 起因の `rest_format_invalid` は再現なし。 |
| workflow path 入口 unblock | 発火相当/非発火相当再実行 | fail | payload drift 起因クラッシュは解消したが、発火相当 run はサーバー混雑と apply 業務バリデーション（email 重複）で workflow 発火確認を完了できず。 |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| `cd e2e && set -a && source .env.local && set +a && ../.venv-server/bin/python src/aica_client/main.py --run-mode TEST` | `apply/finish` が 400（`BasicInfo.email` 重複）で `finish_reason=apply_finish_failed`。 | 検証用ペルソナのメール値を都度ユニーク化するか、既存登録データを初期化して再実行する。 |
| 発火相当再実行 | サーバー混雑エラーメッセージ（`大変混み合っております...`）が継続し、`workflow_received` まで到達した証跡を取得できない。 | サーバー負荷が低い時間帯で再実行し、workflow 発火ログを再採取する。 |

## 未実行

| コマンド | 理由 |
| --- | --- |
| なし | - |

## 免除

| コマンド | オーナー | 理由 | 日付 | フォローアップ |
| --- | --- | --- | --- | --- |
| なし | - | - | - | - |

## 手動確認

- ログ確認:
	- `/tmp/e2e_client/persona_definition_01_bedrock-claude-v1_20260607203047124_c1f869891e5a41b8ba5bceaad8bc0168.log`
	- `/tmp/e2e_client/persona_definition_01_bedrock-claude-v1_20260607203215890_945d6eb830af4eceb4a3bae249f34bfe.log`
- 上記ログで `current_search_filter_loaded` と `jobtype_specific_search_validated` を確認。
- 旧 blocker（`other filter Type ... multi_select`, `NoneType > int`, `Jobtypes must be object`）は再現しないことを確認。
- ただし発火相当 run はサーバー混雑応答が継続し、workflow 発火証跡は未確定。apply フェーズでも業務バリデーション（email 重複）により `apply_finish_failed` を確認。 