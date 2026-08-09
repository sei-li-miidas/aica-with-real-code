# フィーチャー: operational rollback

## 目的

`agent_runtime.service_variant: legacy` への rollback を、実運用で実行できる手順として文書化する。

## 親フェーズ

- フェーズ: phase-6-release-readiness

## スコープ

スコープ内:
- exact config/env override
- restart / rollout / reload 方法
- 確認ログ
- data compatibility assumption
- rollback success criterion
- staging または同等環境での rollback drill 手順

スコープ外:
- 新しい rollback mechanism の実装

## 依存関係

- Phase 5 完了

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-rollback-procedure | rollback procedure を完成させる。 | Phase 5 | operational rollback procedure 確認 | done |

## 完了条件

- pytest evidence だけでなく、運用手順と成功判定が文書化されている。
- rollback drill 手順に、事前状態、config override、反映方法、確認ログ、想定所要時間、成功基準、失敗時の戻し方が含まれている。
- rollback drill を実施できない場合は、実施不能理由と release 判定への影響を `verification.md` に記録する。
