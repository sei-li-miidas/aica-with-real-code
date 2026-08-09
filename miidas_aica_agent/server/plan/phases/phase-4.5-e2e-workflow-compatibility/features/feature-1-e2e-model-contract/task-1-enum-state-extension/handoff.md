# 引き継ぎ: task-1-enum-state-extension

## 概要

`e2e/src/aica_client/models.py` に workflow 互換性のための enum/state 拡張を additive-only で実施した。
`ChatResponseType.WORKFLOW`、`ChatRequestType` の workflow request 2種、`HeadlessState.pending_workflow` を追加し、既存値・既存フィールドは変更していない。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `e2e/src/aica_client/models.py` | `ChatResponseType.WORKFLOW`、`ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED` / `WORKFLOW_CANCELLED`、`HeadlessState.pending_workflow` を追加した。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `ChatResponseType.WORKFLOW = "workflow"`
- `ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED = "workflow_answers_submitted"`
- `ChatRequestType.WORKFLOW_CANCELLED = "workflow_cancelled"`
- `HeadlessState.pending_workflow: dict[str, Any] | None = None`

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| `ChatResponseType` / `ChatRequestType` は既存順序に揃えて値追加のみ実施 | feature-2 側の分岐追加時に既存 contract を壊さず参照できるようにするため | 既存 enum 並び順のリファクタを検討したが、task scope 外かつ rollback risk を増やすため不採用 |
| `pending_workflow` は既存 `pending_*` 群の近傍に追加 | state 読み出し側の可読性と一貫性を維持するため | dataclass 末尾への追加を検討したが、関連フィールドが分散するため不採用 |

## 互換性メモ

- すべての変更が additive であり、既存 enum 値・既存 state フィールドに影響しない。

## 次タスクへのフォローアップ

- `feature-2-e2e-client-workflow-handling` の task-1 は `ChatResponseType.WORKFLOW` を使って `_validate_ws_event_contract()` と `_validate_history_record()` を更新できる。

## 未解決の質問

- なし。

## Review / Fix Log

| Pass | Reviewer | 結果 | 指摘 / 修正 |
| --- | --- | --- | --- |
| 1 | 実装者セルフレビュー | pass | additive-only diff を `git diff --unified=0 -- e2e/src/aica_client/models.py` で確認。削除/置換なしで追加行のみ。 |

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
