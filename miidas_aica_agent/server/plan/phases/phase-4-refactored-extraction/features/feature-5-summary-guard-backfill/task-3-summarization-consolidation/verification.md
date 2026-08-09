# 検証: task-3-summarization-consolidation

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| unit tests (all) | pass | `651 passed` |
| rollback_summary | pass | `17 passed, 890 deselected` |
| pre_extraction_parity | pass | `213 passed, 27 skipped, 667 deselected` |
| integration (test_summary_rollback.py) | pass | `17 passed` |

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
OPENAI_API_KEY="sk-test" PYTHONPATH=server/src/aica_agent \
  .venv-server/bin/python -m pytest -q server/tests/unit/

# rollback_summary
PYTHONPATH=server/src/aica_agent \
  .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/

# pre_extraction_parity
PYTHONPATH=server/src/aica_agent \
  .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/

# integration (summary rollback contract)
OPENAI_API_KEY="sk-test" PYTHONPATH=server/src/aica_agent \
  .venv-server/bin/python -m pytest -v \
    server/tests/integration/chat_service_contract/test_summary_rollback.py
```

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_summary | `pytest -q -m rollback_summary server/tests/` | pass | `17 passed, 890 deselected` |
| pre_extraction_parity | `pytest -q -m pre_extraction_parity server/tests/` | pass | `213 passed, 27 skipped, 667 deselected` |

## 失敗したテスト

なし。

## 未実行

なし。

## 免除

### Coverage 例外（legacy `chat_service.py` の防御分岐）

下記は `pre_extraction_parity` での `services.chat_service` coverage 実行時に未到達となる既知分岐。
task-3 の変更有無に関わらず legacy runtime 側に残る防御パスであり、
Phase 4 task-3 の rollback/parity 完了判定には影響させない。

| branch | reason | owner | date | follow-up |
| --- | --- | --- | --- | --- |
| `server/src/aica_agent/services/chat_service.py:480-481` | `_handle_security_detection()` の想定外例外分岐（`ForbiddenWordDetectedException` 以外）で、通常フローでは呼び出し元がこの分岐へ到達しない。異常系注入専用の防御コード。 | phase-4 feature-5 task-3 owner | 2026-06-04 | Phase 5 `feature-2-coverage-risk-evidence/task-1-coverage-evidence` で fault-injection 可否を再評価。 |
| `server/src/aica_agent/services/chat_service.py:991-1000` | `finalize_stream()` 後段でのみ検知される `ForbiddenWordDetectedException` 分岐。stream 中検知とは別経路で、境界条件付きの再現が必要。現行 rollback/parity は in-stream 検知経路を優先。 | phase-4 feature-5 task-3 owner | 2026-06-04 | Phase 5 で finalization-only security 検知の専用シナリオを追加検討。 |
| `server/src/aica_agent/services/chat_service.py:1031-1032` | post-turn 副作用 (`check_should_start_summary`) の例外ログ分岐。会話本体を失敗させないための best-effort エラーハンドリングで、parity command では意図的に fault 注入していない。 | phase-4 feature-5 task-3 owner | 2026-06-04 | Phase 5 coverage evidence で summary side-effect fault injection test の追加可否を判断。 |

## 手動確認

なし。
