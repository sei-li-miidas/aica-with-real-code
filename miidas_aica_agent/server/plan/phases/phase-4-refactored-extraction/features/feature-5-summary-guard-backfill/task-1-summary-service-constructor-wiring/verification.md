# 検証: task-1-summary-service-constructor-wiring

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| unit tests (chat_service_refactored) | pass | `43 passed in 1.38s` |
| rollback_di | pass | `41 passed, 876 deselected in 1.95s` |
| rollback_summary | pass | `15 passed, 902 deselected in 1.56s` |
| pre_extraction_parity | pass | `211 passed, 27 skipped, 679 deselected in 4.23s` |

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

```bash
# unit tests
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q \
  server/tests/unit/services/test_chat_service_refactored.py

# rollback_di — Container.chat_svc() がコンストラクタ TypeError なしに解決できることを確認
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/

# rollback_summary
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/

# pre_extraction_parity
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/
```

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_di | `pytest -q -m rollback_di server/tests/` | pass | `41 passed, 876 deselected`。`model_list` 未設定時でも `chat_svc` 解決可能。 |
| rollback_summary | `pytest -q -m rollback_summary server/tests/` | pass | `15 passed, 902 deselected`。summary rollback 回帰なし。 |

## 失敗したテスト

なし。

## 未実行

なし。

## 免除

なし。

## 手動確認

- `chat_service_refactored.ChatService` constructor が以下を満たすことを確認:
  - `llm_output_guard` 注入時は注入インスタンスを使用。
  - 未注入時は `LLMOutputGuard()` をローカル生成。
  - `summary_service` 注入時は `self._summary_service` に保持。
  - 未注入時は `self._summary_service is None`。
