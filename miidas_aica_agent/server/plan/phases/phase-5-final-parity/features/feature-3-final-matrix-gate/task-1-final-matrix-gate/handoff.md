# 引き継ぎ: task-1-final-matrix-gate

## 概要

Phase 5 feature-3 task-1 として、final matrix gate の release 判定に必要な証跡を最新実行結果で固定した。`gate_a_scenario_matrix.md` の required scenario matrix で `pending-phase-4` が残っていた行（startup/default/endpoint/DI）を `pass` に更新し、final gate の集約実行ログと判定を追記した。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/plan/phases/gate_a_scenario_matrix.md` | final matrix gate の集約実行ログと release gate 判定を追加。required scenario matrix の不足していた real-refactored evidence を `pass` へ更新。 |
| `server/plan/phases/phase-5-final-parity/features/feature-3-final-matrix-gate/task-1-final-matrix-gate/verification.md` | 必須コマンドと rollback サブセット結果を実行値で記録し、未実行/失敗/免除を解消。 |
| `server/plan/phases/status.md` | phase-5 feature-3 task-1 のステータスを `done` に更新し、フェーズ要約を final matrix gate 完了状態へ更新。 |
| `server/plan/phases/phase-5-final-parity/features/feature-3-final-matrix-gate/task-1-final-matrix-gate/handoff.md` | 本タスクの引き継ぎ情報を実値で更新。 |

## 新しいAPI / ヘルパー / フィクスチャ

- なし（ドキュメント証跡更新のみ）。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| final gate では matrix 証跡を command-first で再固定する | feature-2 の証跡を参照するだけだと、Phase 5 終了時点の最終 pass 判定が曖昧になるため。 | feature-2 の既存ログのみ参照して更新しない（不採用）。 |
| rollback サブセットを全件再実行する | critical scenario の `pass` 判定を subset 単位で再確認し、blocked 判定条件を確実に満たすため。 | `pre_extraction_parity` だけ再実行する（不採用）。 |
| coverage コマンドも final gate で再実行する | 親 phase README の required verification 整合を final gate 時点で明示するため。 | feature-2 の coverage 記録を流用する（不採用）。 |

## 互換性メモ

- 本タスクはコード挙動を変更していない。ドキュメント上の final evidence と release 判定を更新したのみ。
- 既存 waiver は増やしていない。critical scenario の waiver は 0 件を維持。

## 次タスクへのフォローアップ

- Phase 6 task-1 以降では、本タスクの `Release gate 判定 (2026-06-08)` を Gate A release candidate 判定の参照元として利用する。
- Phase 6 で運用手順書を作る際、`rollback_endpoint_config` / `rollback_di` / `rollback_runner` / `rollback_security` / `rollback_summary` の最新 pass 結果を再利用できる。

## 未解決の質問

- なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
