# 引き継ぎ: task-1-contract-validation-updates

## 概要

`_validate_ws_event_contract()` に WORKFLOW 用の contract validation branch を加算し、
`_validate_history_record()` の許容 type に `ChatResponseType.WORKFLOW` を追加した。
既存の validation 分岐は削除・変更せず保持した。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `e2e/src/aica_client/client/e2e_client.py` | `_validate_ws_event_contract()` に WORKFLOW payload の `"id"` フィールド検証 branch を追加した。`_validate_history_record()` の許容型 set に `ChatResponseType.WORKFLOW` を追加した。 |

## 新しいAPI / ヘルパー / フィクスチャ

- なし（既存メソッドへの additive 変更のみ）

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| WORKFLOW event は `event.message` を JSON parse した payload の `id` 必須検証のみ追加する | task.md の required implementation detail に一致させ、task-2 での state 更新/dispatch 追加と責務を分離するため | models 側を先に拡張する案は task scope 外のため不採用 |

## 互換性メモ

- すべての変更が additive であり、既存の検証ロジックに影響しない。

## 次タスクへのフォローアップ

- `task-2-workflow-receive-dispatch-send` は `_update_state_from_exchange()`、`_handle_workflow()`、`_handle_pending_actions()` を追加する。

## 未解決の質問

- なし。

## Review / Fix Log

| Pass | Reviewer | 結果 | 指摘 / 修正 |
| --- | --- | --- | --- |
| 1 | task owner | clean | additive-only 変更で既存 validation 分岐を保持。追加要件（WORKFLOW payload `id` 検証・history type 拡張）を満たすことを確認。 |

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
