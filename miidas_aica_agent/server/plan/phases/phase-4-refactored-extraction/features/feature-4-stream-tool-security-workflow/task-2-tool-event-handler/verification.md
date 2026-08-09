# 検証: task-2-tool-event-handler

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/unit/services/chat/test_tool_event_handler.py -q --cov=services.chat.tool_event_handler --cov-branch --cov-fail-under=100` | pass | 51 passed, branch coverage 100% (126 statements, 48 branches) |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity` | pass | 179 passed, 58 skipped（前回 173 → +6、tool result real-refactored 3 テスト解除） |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m rollback_runner` | pass | 32 passed（前回 29 → +3、tool result real-refactored 3 テスト解除） |

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
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/unit/services/chat/test_tool_event_handler.py -q --cov=services.chat.tool_event_handler --cov-branch --cov-fail-under=100` | pass | 51 passed, 100% branch coverage |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity` | pass | 179 passed, 58 skipped |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m rollback_runner` | pass | 32 passed |

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_runner | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m rollback_runner` | pass | 32 passed |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity` | pass | 179 passed, 58 skipped |

## 失敗したテスト

なし。

## 未実行

なし。

## 免除

なし。

## 手動確認

- `gate_a_scenario_matrix.md` の `tool result response shape` real-refactored evidence を `pass: pytest -q -m pre_extraction_parity` に更新済み。
- `status.md` の task-2-tool-event-handler を `done` に更新済み。
- feature README の task-2 ステータスを `done` に更新済み。
- `chat_service_refactored.py` の rate-limit 例外ハンドリングを修正済み（`PositionSearchRateLimitExceeded` を generic `Exception` より先に catch）。

## 既知の動作差異

| 項目 | 現在の動作 | legacy | 解決 task | parity gate への影響 |
| --- | --- | --- | --- | --- |
| ツール実行失敗（`"Message"` キー） | warning ログのみ、LLM リトライ起動なし | `llm_error = True` でリトライループ起動 | task-5 以降（リトライループ実装時） | `pre_extraction_parity` に当該パスのテストなし。現行 gate は通過。 |
