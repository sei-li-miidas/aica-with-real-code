# 引き継ぎ: task-2-legacy-delegating-characterization

## 概要

task-2 では、task-1 で作成した scaffold test を実行可能な characterization suite へ更新した。`pre_extraction_parity` marker で legacy/delegating の evidence を記録し、`real-refactored` は `pending-phase-4` として明示した。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/tests/integration/chat_service_contract/conftest.py` | variant-aware な `chat_service_container` fixture を追加し、legacy/delegating の service 解決を固定。 |
| `server/tests/integration/chat_service_contract/test_db_side_effects.py` | scaffold skip を解除し、fixture contract characterization assertion を実装。 |
| `server/tests/integration/chat_service_contract/test_history_mapping.py` | scaffold skip を解除し、history mapping contract の characterization assertion を実装。 |
| `server/tests/integration/chat_service_contract/test_tool_results.py` | scaffold skip を解除し、tool result shape contract の characterization assertion を実装。 |
| `server/tests/integration/chat_service_contract/test_security_cleanup.py` | scaffold skip を解除し、security/cancellation fixture contract assertion を実装。 |
| `server/tests/integration/chat_service_contract/test_workflow_side_effects.py` | scaffold skip を解除し、workflow side effects contract assertion を実装。 |
| `server/tests/integration/chat_service_contract/test_summary_rollback.py` | scaffold skip を解除し、summary rollback contract assertion を実装。 |
| `server/tests/integration/chat_service_contract/test_no_legacy_dependency.py` | Phase 3 範囲の placeholder characterization を実装し、Phase 4 proof へ引き継ぐ前提を明記。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | Phase 3 owner 分シナリオの legacy/delegating evidence を更新。 |
| `server/plan/phases/phase-3-runner-contract-pre-extraction/features/feature-2-pre-extraction-parity/task-2-legacy-delegating-characterization/verification.md` | 必須コマンドと検証結果を更新。 |
| `server/plan/phases/status.md` | task-2 のステータスを更新。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `chat_service_container` fixture (`server/tests/integration/chat_service_contract/conftest.py`):
	- `variant=legacy` -> `service_variant=legacy` を解決
	- `variant=delegating-refactored` -> `service_variant=refactored` (Phase 2 delegating adapter)
	- `variant=real-refactored` -> `pending-phase-4` として skip

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| Phase 3 は fixture contract characterization を採用 | task-1 で定義した scaffold fixture (`_expected_keys`) を source of truth とし、Phase 4 で behavior proof を追加する計画に合わせるため。 | task-2 で full behavior assertion まで実装する案。Phase 4/5 の抽出・proof task と責務重複するため不採用。 |
| variant-aware fixture で module identity をチェック | legacy/delegating の wiring が壊れても false-green にならない最小 guard を入れるため。 | テスト本体で毎回 module 判定を重複記述する案。重複が増えるため不採用。 |

## 互換性メモ

- production code / public API の変更はなし。test/doc のみ更新。
- `pre_extraction_parity` 実行では `real-refactored` は Phase 4 owner が証跡を埋める前提で skip。

## 次タスクへのフォローアップ

- task-3 で private test migration map を更新するとき、今回追加した characterization test と fixture path を移行元/移行先マッピングへ反映する。
- Phase 4 bootstrap task で `test_no_legacy_dependency.py` を behavior proof (LLMRunner 到達と delegating 差分 fail) に昇格させる。
- Phase 4/5 owner は `gate_a_scenario_matrix.md` の `real-refactored evidence` を `pending-phase-4` から更新する。

## 未解決の質問

- なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
