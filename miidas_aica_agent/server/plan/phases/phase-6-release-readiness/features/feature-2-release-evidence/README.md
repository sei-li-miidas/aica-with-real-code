# フィーチャー: release evidence

## 目的

Gate A release candidate に必要な logging evidence と release candidate verification checklist を揃える。

## 親フェーズ

- フェーズ: phase-6-release-readiness

## スコープ

スコープ内:
- startup log evidence
- chat turn log evidence
- matrix completion confirmation
- release candidate verification checklist

スコープ外:
- implementation refactor
- Phase 1-5 gate の再設計

## 依存関係

- feature-1-operational-rollback

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-release-logging-and-verification | logging evidence と RC verification checklist を揃える。 | operational rollback | logging evidence / RC verification checklist | done |

## 完了条件

- startup log と chat turn log の evidence が記録されている。
- Phase 1-5 gate command の再実行結果は RC verification checklist として記録されている。
- RC verification checklist は Phase 6 の新規成果物と分離され、失敗または未実行があれば release candidate を作らない。
