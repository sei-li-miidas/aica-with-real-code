# 引き継ぎ: task-2-workflow-receive-dispatch-send

## 概要

`e2e_client.py` に workflow receive/dispatch/send を additive-only で実装した。
`_update_state_from_exchange()` で `WORKFLOW` event を `pending_workflow` へ保持し、
`_handle_pending_actions()` の先頭で workflow を優先 dispatch して
`_handle_workflow()` から `WORKFLOW_ANSWERS_SUBMITTED` を送信する。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `e2e/src/aica_client/client/e2e_client.py` | `_update_state_from_exchange()` に WORKFLOW branch を追加し、`state.pending_workflow` に JSON parsed payload を設定するようにした。 |
| `e2e/src/aica_client/client/e2e_client.py` | `_handle_workflow()` を新規追加した。workflow の最初のオプション値を使って answers dict を構築し、`WORKFLOW_ANSWERS_SUBMITTED` payload を `_send_ws_action()` 経由で送信する。 |
| `e2e/src/aica_client/client/e2e_client.py` | `_handle_pending_actions()` の先頭に `pending_workflow` dispatch を追加した。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `async def _handle_workflow(self, workflow: dict[str, Any]) -> None`
  - workflow answers を自動 submit する async メソッド。`_send_ws_action()` が async のため async にする。デフォルトポリシーは常に submit。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| デフォルトポリシーは常に submit | `_handle_jobtype_search_result()` の先例に倣い、e2e が常に先に進めるようにする。 | cancel path を実装する（Phase 4.5 scope 外）。 |
| workflow dispatch を pending action の先頭に置く | task.md の required snippet に合わせ、既存 pending action（jobtype/search_link/search_result）を変更せず優先順だけ追加するため。 | 既存 dispatch 順を維持する案（task 要件不一致のため不採用）。 |

## 互換性メモ

- `_handle_pending_actions()` への dispatch は既存の `if self.state.pending_jobtype_search:` の前に挿入されるため、他の pending action との優先順位は workflow が先になる。

## 次タスクへのフォローアップ

- Phase 5 の final parity suite と e2e 実行に進む前提として、workflow path の互換性ギャップが解消されている。

## 未解決の質問

- なし。

## Review / Fix Log

| Pass | Reviewer | 結果 | 指摘 / 修正 |
| --- | --- | --- | --- |
| 1 | task owner | clean | スコープ内 3 箇所のみを additive で実装。disallowed 変更（`models.py`、validation branch、既存 dispatch 改変）なしを確認。 |

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
