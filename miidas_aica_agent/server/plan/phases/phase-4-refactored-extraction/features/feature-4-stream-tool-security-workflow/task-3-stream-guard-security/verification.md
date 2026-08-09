# 検証: task-3-stream-guard-security

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `pytest -q -m rollback_security --ignore=cli` | pass | 33 passed, 9 skipped（skipped は task-4 workflow の real-refactored variants） |
| `pytest --cov=services.chat.stream_guard --cov-branch --cov-fail-under=100 server/tests/unit/services/chat/test_stream_guard.py` | pass | 20 passed, 100% branch coverage |
| `pytest -q --ignore=cli` | pass | 752 passed, 53 skipped, 0 failed |

## 必須コマンド

```
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security --ignore=cli
```

結果: 33 passed, 9 skipped, 779 deselected (2026-05-26)

```
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --cov=services.chat.stream_guard --cov-branch --cov-fail-under=100 server/tests/unit/services/chat/test_stream_guard.py
```

結果: 20 passed, 100% branch coverage (2026-05-26)

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_security | `pytest -q -m rollback_security --ignore=cli` | pass | 33 passed, 9 skipped（9 skipped は task-4 workflow real-refactored） |
| pre_extraction_parity | `pytest -q -m pre_extraction_parity --ignore=cli` | pass | 基本 parity 維持確認済み |

## 失敗したテスト

なし

## 未実行

なし

## 免除

なし（unit test branch coverage 100% 達成済み）

## 手動確認

- `test_security_cleanup.py` の real-refactored 5 variants がすべて pass することを確認
- legacy/delegating-refactored variants の既存 13 tests がすべて pass することを確認（リグレッションなし）
