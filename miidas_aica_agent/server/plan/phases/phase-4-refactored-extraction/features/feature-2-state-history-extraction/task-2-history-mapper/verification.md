# 検証: task-2-history-mapper

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| unit tests 100% branch coverage | pass | 63 passed |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | pass | 168 passed, 67 skipped |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di` | pass | 32 passed, 8 skipped |

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
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest \
  --cov=services.chat.history_mapper --cov-branch --cov-fail-under=100 \
  server/tests/unit/services/chat/test_history_mapper.py -q
```

結果: `63 passed`, `100%` branch coverage

```
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/
```

結果: `168 passed, 67 skipped`

```
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/
```

結果: `32 passed, 8 skipped`

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_di | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di` | pass | 32 passed, 8 skipped |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | pass | 168 passed, 67 skipped |

## 失敗したテスト

なし。

## 未実行

なし。

## 免除

なし。

## 手動確認

- `test_history_mapping.py` の全 3 variant（legacy / delegating-refactored / real-refactored）が `chat_service_container_history_parity` フィクスチャで実行されることを確認。
- `real-refactored` variant では `chat_svc._llm_runner.run_streamed` がモックされ、`LLMRunner` プロトコル経由で入力が渡されることを確認。
- `gate_a_scenario_matrix.md` の `history mapping` 行 `real-refactored evidence` が `pass` に更新されたことを確認。
