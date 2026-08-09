# 引き継ぎ: task-2-bootstrap-behavioral-proof

## 概要

`test_no_legacy_dependency.py` の pending skip テスト 3 件を実装し、`LLMRunner.run_streamed()` 到達 behavioral proof を追加した。

- `test_real_refactored_reaches_llm_runner`: `real-refactored` mode で `run_streamed` が 1 回呼ばれることを spy で検証。
- `test_real_refactored_vs_delegating_adapter_difference`: `_delegate_chat=True`（Phase 2 delegating adapter 復元相当）では `run_streamed` が呼ばれず、ポジティブ assertion が `AssertionError` で fail することを `pytest.raises` で検証する negative test。
- `test_real_refactored_execution_identity`: module identity・`_delegate_chat=False`・`_llm_runner` inject を検証。

`gate_a_scenario_matrix.md` の `legacy dependency reintroduction` row の `real-refactored evidence` を `pending-phase-4` から `pass` に更新した。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/tests/integration/chat_service_contract/test_no_legacy_dependency.py` | pending skip テスト 3 件を実装。behavioral proof と negative test を追加。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | `legacy dependency reintroduction` の `real-refactored evidence` を `pass` に更新。 |
| `server/plan/phases/phase-4-refactored-extraction/features/feature-1-refactored-bootstrap/README.md` | task-2 status を `done` に更新。 |
| `server/plan/phases/phase-4-refactored-extraction/features/feature-1-refactored-bootstrap/task-2-bootstrap-behavioral-proof/verification.md` | 必須コマンド結果、behavioral proof 証跡を記録。 |
| `server/plan/phases/status.md` | phase-4 task-2 row を `done` に更新。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `_FakeRunStream` (test-local): stream_events が何も yield しない最小 run stream fake。behavioral proof で `run_streamed` の返り値として使う。
- `_init_chat_session` (test-local helper): init_session + state flag セット。positive/negative テストで共通利用。
- `_empty_delegating_chat` (test-local): `if False: yield` で何も yield しない async generator。negative test で `legacy.chat` を差し替える。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| `_delegate_chat=True` でも同一 fixture setup を使い、`monkeypatch.setattr(legacy, "chat", ...)` で legacy.chat をスタブする | negative test が full legacy state setup を必要とせず、routing の切り替えだけに集中できるため。 | legacy path を full state setup で通す（session/history/runner のモックが複雑になる）。 |
| negative test は `run_streamed.call_count == 0` assertion + `pytest.raises(AssertionError)` の両方を使う | delegating mode で run_streamed が呼ばれないことを明示し、かつポジティブ assertion が fail することを explicit に示すため。 | `run_streamed.call_count == 0` のみ（ポジティブ assertion の failure が明示されない）。 |
| static import check は実装しない | task.md の注記どおり、behavioral proof の代替として使ってはならず、補助防御として optional。behavioral proof のみで完全な証拠を得られるため。 | `chat_service_refactored.py` が `chat_service.ChatService` を import しないことを `grep` で確認する。 |

## 互換性メモ

- `pre_extraction_bootstrap` は 4 passed + 3 skipped → 7 passed に変化した。parity regression なし。
- `pre_extraction_parity` は 165 passed, 70 skipped（task-1 時点から微増；task-2 の 3 件が parity にも属しているため）。

## 次タスクへのフォローアップ

- feature-1 は完了。feature-2 (`ConversationState`) から phase-4 の extraction 作業へ進む。
- `chat_service_refactored.py` はまだ legacy helper/state を多数保持しているため、feature-2 以降は bootstrap shell の public behavior を壊さずに component 分離を進める。

## 未解決の質問

なし

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
