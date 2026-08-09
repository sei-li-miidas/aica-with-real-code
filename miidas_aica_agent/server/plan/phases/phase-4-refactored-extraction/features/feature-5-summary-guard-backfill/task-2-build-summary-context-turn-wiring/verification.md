# 検証: task-2-build-summary-context-turn-wiring

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| unit tests (chat_service_refactored) | pass | `46 passed in 1.43s` |
| rollback_summary (real-refactored evidence) | pass | `17 passed, 905 deselected in 1.93s` |
| pre_extraction_parity | pass | `213 passed, 27 skipped, 682 deselected in 4.20s` |

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

# rollback_summary (real-refactored evidence)
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/

# pre_extraction_parity
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/
```

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_summary | `pytest -q -m rollback_summary server/tests/` | pass | `test_summary_rollback.py` に real-refactored の chat() summary wiring evidence（2 tests）を追加し、marker 全体を green 化。 |

## gate_a_scenario_matrix.md 更新

- `summary_rollback` の `real-refactored evidence` を、chat() summary wiring proof を含む最新実行結果へ更新済み。

## 失敗したテスト

なし。

## 未実行

なし。

## 免除

なし。

## 手動確認

- `chat_service_refactored.ChatService.chat()` の順序確認:
  - `prepare_turn()` 後に summary context 再構築分岐が入ること
  - `_record_usage()` 後、`should_save = True` 前に summary 起動判定分岐が入ること
