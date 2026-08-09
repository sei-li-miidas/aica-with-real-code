# 引き継ぎ: task-3-test-migration-map

## 概要

task-3 では、Phase 4 extraction task が参照する `test_migration_map.md` を新規作成し、legacy テスト在庫（`server/tests/unit/services/test_chat_service.py`）を migration target へ割り当てた。
併せて、`gate_a_scenario_matrix.md` と整合する evidence 表現（`pass` / `fixture-schema-only` / `pending-phase-4`）に統一した。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/plan/phases/phase-3-runner-contract-pre-extraction/features/feature-2-pre-extraction-parity/task-3-test-migration-map/test_migration_map.md` | legacy test class（14 classes / 62 tests）在庫、Phase 4 owner task への migration map、required marker・scenario 対応表を作成。 |
| `server/plan/phases/phase-3-runner-contract-pre-extraction/features/feature-2-pre-extraction-parity/task-3-test-migration-map/verification.md` | 実行コマンド、waiver、not-applicable 判定を記録。 |
| `server/plan/phases/status.md` | task-3 のステータスを更新。 |

## 新しいAPI / ヘルパー / フィクスチャ

- なし（本 task は計画文書のみ更新）。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| evidence 表現を `pass` / `fixture-schema-only` / `pending-phase-4` に限定 | `gate_a_scenario_matrix.md` と矛盾しない表現へ統一するため。 | `pass (Phase 3 characterization)` のような自由記述。解釈の揺れが出るため不採用。 |
| migration map を test class 単位 + behavior 単位で併記 | private method 名だけでは Phase 4 owner がテスト移行範囲を誤るため。 | private method 列のみで管理。網羅性確認が難しいため不採用。 |
| 未分類行を残さず owner task へ割当 | task 完了条件「未分類の affected private test を残さない」を満たすため。 | 「未分類」セクションを残す。完了条件違反となるため不採用。 |

## 互換性メモ

- production code / public API 変更なし。
- ドキュメントのみ更新。

## 次タスクへのフォローアップ

- Phase 4 各 owner は `test_migration_map.md` の自タスク該当行を source of truth として、component unit test へ移行する。
- real-refactored 実行証跡は本 task では更新しない。Phase 4/5 owner が `gate_a_scenario_matrix.md` の `real-refactored evidence` を更新する。

## 未解決の質問

- なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
