# 引き継ぎ: task-1-integration-pr-readiness

## 概要

Gate A release candidate を `develop` へ統合するための readiness を固定した。

作業内容:
- release notes を新規作成し、Gate A RC の範囲と Gate B handoff assumptions を明示した。
- develop 統合 PR の evidence checklist を新規作成し、rollback / logging / verification / matrix の参照先を固定した。
- `gate_a_scenario_matrix.md` に integration PR readiness の確認メモを追記した。
- phase / feature / task の status を `done` に更新した。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/plan/phases/phase-6-release-readiness/features/feature-3-develop-integration/task-1-integration-pr-readiness/release-notes.md` | Gate A RC の release note と Gate B handoff assumptions を記録。 |
| `server/plan/phases/phase-6-release-readiness/features/feature-3-develop-integration/task-1-integration-pr-readiness/pr-evidence-checklist.md` | develop 統合 PR に必要な evidence checklist を記録。 |
| `server/plan/phases/phase-6-release-readiness/features/feature-3-develop-integration/task-1-integration-pr-readiness/handoff.md` | 完了後の引き継ぎ情報を実値へ更新。 |
| `server/plan/phases/phase-6-release-readiness/features/feature-3-develop-integration/task-1-integration-pr-readiness/verification.md` | release notes / checklist / matrix / handoff assumptions の完了判定を記録。 |
| `server/plan/phases/phase-6-release-readiness/features/feature-3-develop-integration/README.md` | feature task status を `done` に更新。 |
| `server/plan/phases/phase-6-release-readiness/README.md` | feature-3 の feature status を `done` に更新。 |
| `server/plan/phases/status.md` | phase-6 feature-3 task-1 を `done` に更新。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | Phase 6 integration PR readiness memo を追加。 |

## 新しいAPI / ヘルパー / フィクスチャ

- なし。ドキュメント/evidence 更新のみ。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| release notes と PR evidence checklist を別ファイルに分離した | release note は release candidate の境界と Gate B handoff assumptions を説明し、checklist は参照先と pass 判定を機械的に追えるようにするため。 | 1 ファイルに統合する。読みやすさと後続参照性が下がるため不採用。 |
| matrix には新しい runtime evidence ではなく integration readiness memo を追記した | この task は Gate A の新規実装ではなく、release readiness のまとめであり、既存の final evidence を再度記録するのではなく、PR readiness の集約が必要だから。 | matrix を変更しない。task 要件にある matrix 更新が満たせないため不採用。 |
| Gate B handoff assumptions は release notes に明示した | 次のフェーズの開始条件をこの task の成果物に残しておくと、develop integration PR から Gate B への引き継ぎが切れないため。 | handoff assumptions を口頭でのみ共有する。文書化要件を満たさないため不採用。 |

## 互換性メモ

- Gate A release candidate の対象は既存の rollback / logging / verification evidence で変わらない。
- Gate B はこの PR のスコープ外であり、runtime behavior 変更は別の planning / evidence cycle を要する。

## 次タスクへのフォローアップ

- develop 統合 PR を作成する際は、本 task の release notes と PR evidence checklist を添付し、Gate B は別計画として切り離す。

## 未解決の質問

- なし。PR readiness に必要な成果物は揃った。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
