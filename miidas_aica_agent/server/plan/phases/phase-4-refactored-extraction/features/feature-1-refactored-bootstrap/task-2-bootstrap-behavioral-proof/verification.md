# 検証: task-2-bootstrap-behavioral-proof

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `export PYTHONPATH=server/src/aica_agent && .venv-server/bin/python -m pytest -v server/tests/integration/chat_service_contract/test_no_legacy_dependency.py` | pass | `3 passed` |
| `export PYTHONPATH=server/src/aica_agent && .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap server/tests/` | pass | `7 passed, 527 deselected`（task-1 の 4 passed + 3 skipped が 7 passed に変化） |
| `export PYTHONPATH=server/src/aica_agent && .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/` | pass | `165 passed, 70 skipped, 299 deselected`（parity regression なし） |

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
| `export PYTHONPATH=server/src/aica_agent && .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap server/tests/` | pass | `7 passed, 527 deselected` |
| `export PYTHONPATH=server/src/aica_agent && .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/` | pass | `165 passed, 70 skipped, 299 deselected` |

## Component Branch Coverage

| 対象 | 結果 | 理由 |
| --- | --- | --- |
| `services.chat_service_refactored` | not-applicable | このタスクは behavioral proof 主体であり、component extraction が対象ではない。親 feature README Coverage Policy §3「対象外タスク」に該当するため coverage gate は not-applicable。 |

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| `pre_extraction_bootstrap` | `export PYTHONPATH=server/src/aica_agent && .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap server/tests/` | pass | `legacy dependency reintroduction` の real-refactored evidence が `pass` に更新された。 |

## Behavioral Proof 証跡

| テスト | 証明内容 | 結果 |
| --- | --- | --- |
| `test_real_refactored_reaches_llm_runner` | `real-refactored` mode で `LLMRunner.run_streamed()` が 1 回呼ばれることを spy で検証 | pass |
| `test_real_refactored_vs_delegating_adapter_difference` | `_delegate_chat=True`（delegating adapter 相当）では `run_streamed` が呼ばれず、ポジティブ assertion が `AssertionError` で fail することを `pytest.raises` で検証 | pass |
| `test_real_refactored_execution_identity` | module が `services.chat_service_refactored`、`_delegate_chat=False`、`_llm_runner` が inject 済みであることを検証 | pass |

## 失敗したテスト

なし

## 未実行

なし

## 免除

なし

## 手動確認

- `pre_extraction_bootstrap` の 3 skipped（task-1 時点で skip だったもの）がすべて `pass` に変化し、7 passed となった。
- `pre_extraction_parity` は 165 passed, 70 skipped で regression なし（task-1 時点の 162 passed, 73 skipped から微増；差分は task-2 の新規テスト 3 件が `pre_extraction_parity` にも属しているため）。
- static import check は追加防御として許可されるが本 task では実施しない（behavioral proof のみで十分）。
