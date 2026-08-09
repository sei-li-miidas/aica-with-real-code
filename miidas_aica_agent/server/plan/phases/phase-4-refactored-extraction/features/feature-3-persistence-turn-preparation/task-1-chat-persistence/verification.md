# 検証: task-1-chat-persistence

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --cov=services.chat.chat_persistence --cov-branch --cov-fail-under=100 server/tests/unit/services/chat/test_chat_persistence.py` | pass | 45 passed, 100% branch coverage |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/test_db_side_effects.py` | pass | 17 passed (legacy 5 + delegating-refactored 5 + real-refactored 7) |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/` | pass | 173 passed, 61 skipped |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/` | pass | 29 passed, 3 skipped |

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
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --cov=services.chat.chat_persistence --cov-branch --cov-fail-under=100 server/tests/unit/services/chat/test_chat_persistence.py` | pass | 45 passed, 100% branch coverage (89 stmts, 36 branches, 0 missing) |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/integration/chat_service_contract/test_db_side_effects.py` | pass | 17 passed |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/` | pass | 173 passed, 61 skipped |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/` | pass | 29 passed, 3 skipped |

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_runner | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/` | pass | 29 passed, 3 skipped |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/` | pass | 173 passed, 61 skipped |

## 失敗したテスト

なし。全コマンドで pass を確認。

## 未実行

なし。

## 免除

なし。

## 手動確認

- `test_db_side_effects.py` の `real-refactored` バリアントが `chat_service_container_db_side_effects` fixture 経由で実行され、`_delegate_chat=True` を設定せずに real refactored パスを通ることを確認した。
- `ChatPersistence.create_session()` 実行後に `legacy._session_created` に同期していることを `test_create_session_sets_session_created` で確認した。
- `test_db_retry_error_save` は real-refactored バリアントを含まない（リトライループが存在しないため `not-applicable`）。
