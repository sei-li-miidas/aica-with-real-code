# Gate A タスクステータス

## 概要

- ゲート:
- 中間ブランチ:
- 最終更新:
- 現在のフェーズ:
- 現在のリスク:

## ステータス表

| フェーズ | フィーチャー | タスク | ステータス | オーナー | ブランチ/PR | 引き継ぎ | 検証 | メモ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phase-x | feature-y | task-z | not-started | 未割当 | 未割当 | `server/plan/phases/.../handoff.md` | `server/plan/phases/.../verification.md` |  |

## ステータス値

- `not-started`
- `ready`
- `in-progress`
- `blocked`
- `review`
- `done`

完了ルール:
- `verification.md` で、すべての必須コマンドが `pass`、`waived`、または `not-applicable` と示されていない限り、`done` は無効。
- `waived` には、オーナー、理由、日付、フォローアップが必要。
- `not-applicable` には理由が必要。
- 必須コマンドに `fail` または `not-run` がある場合、ステータスは `done` ではなく、`blocked`、`in-progress`、または `review` にする必要がある。

## ブロッカー

| 項目 | オーナー | ブロック理由 | 必要な判断 | 発生日 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
