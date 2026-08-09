# 検証: task-2-turn-preparer

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| unit tests (turn_preparer + conversation_state + chat_service_refactored) | pass | 89 passed |
| branch coverage 100% (turn_preparer) | pass | 72 stmts, 26 branches, 0 missing |
| pre_extraction_parity | pass | 173 passed, 61 skipped |
| rollback_runner | pass | 29 passed, 3 skipped |

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

```
# unit tests
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q \
  server/tests/unit/services/chat/test_turn_preparer.py \
  server/tests/unit/services/chat/test_conversation_state.py \
  server/tests/unit/services/test_chat_service_refactored.py
# → 89 passed in 1.55s

# branch coverage 100%
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest \
  --cov=services.chat.turn_preparer --cov-branch --cov-fail-under=100 \
  --cov-report=term-missing \
  server/tests/unit/services/chat/test_turn_preparer.py
# → 26 passed, 100% (72 stmts, 26 branches, 0 missing)

# pre_extraction_parity
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/
# → 173 passed, 61 skipped

# rollback_runner
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/
# → 29 passed, 3 skipped
```

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_runner | `pytest -q -m rollback_runner server/tests/` | pass | 29 passed, 3 skipped |

## 失敗したテスト

なし。

## 未実行

なし。

## 免除

なし。

## 手動確認

- parity test `test_refactored_bootstrap_shell.py` の `inner._previous_response_ids` / `inner._conversation` アサーションを `chat_svc._conv_state.*` に更新（alias 廃止に対応）。テスト自体の意図（runner 実行後のステート検証）は変わっていない。
