# 引き継ぎ: task-1-final-contract-suite

## 概要

Phase 5 feature-1 task-1 の必須検証コマンドを実行し、
final contract suite の pass evidence を `gate_a_scenario_matrix.md` へ追記した。

本タスクでは production code / test code への変更は行わず、
計画文書の evidence 更新に集中した。

実行メタ情報:
- 実行者: `sei.li@miidas.jp`
- 実行ブランチ: `feature/77996_chat_service_refactoring_phase_5_feature_1_task_1`

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/plan/phases/phase-5-final-parity/features/feature-1-final-parity-scenarios/task-1-final-contract-suite/handoff.md` | task-1 の引き継ぎ内容を実績値へ更新。 |
| `server/plan/phases/phase-5-final-parity/features/feature-1-final-parity-scenarios/task-1-final-contract-suite/verification.md` | required command の実行結果と rollback subset 結果を記録。 |
| `server/plan/phases/status.md` | phase-5 feature-1 task-1 を `done` へ更新。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | final contract suite 実行結果の scenario evidence 行を追記。 |

## 新しいAPI / ヘルパー / フィクスチャ

なし。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| final contract suite では marker command を source of truth とする | task 要件が `pre_extraction_parity` と `rollback_summary` の必須実行を要求しているため。 | 個別 test file 単位の再実行。今回は task 定義の必須コマンドを優先した。 |
| evidence は matrix に日付付きで追加し、既存履歴は保持する | 過去フェーズの証跡を破壊せず、Phase 5 final parity の最新実行結果を明示するため。 | 既存 evidence 文字列の全面置換。履歴可読性が下がるため不採用。 |

## 互換性メモ

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` は `153 passed, 8 skipped, 668 deselected`。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` は `12 passed, 817 deselected`。
- final contract suite の required command では回帰を検出していない。

## 次タスクへのフォローアップ

- `task-2-critical-scenario-evidence` では、本タスクで追記した matrix evidence を基準に critical scenario の `pass` 固定を仕上げること。
- feature README の task table status が `not-started` のままなので、task-2 開始時に必要なら feature-level status も同期すること。

## 未解決の質問

なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
