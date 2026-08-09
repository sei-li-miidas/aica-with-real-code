# フェーズ: e2e workflow 互換性ギャップ解消

## 目的

Phase 4 で独立実装化した refactored 実体が発火する workflow 系イベントに対して、`e2e/` headless client 側の contract を追随させる。Phase 5 の最終 parity suite と e2e 実行に進む前に、`WORKFLOW` response / `WORKFLOW_ANSWERS_SUBMITTED` / `WORKFLOW_CANCELLED` request の enum 不整合と dispatch ロジックの欠如を解消する。

また、workflow verification に先行する REST 初期化経路で contract drift が見つかった場合、その blocker 解消も本 phase で扱う。workflow path に到達する前の既存 e2e contract mismatch は、本 phase の verification を成立させる前提条件として明示的に解消する。

## スコープ

スコープ内:
- `e2e/src/aica_client/models.py` の enum と state 拡張
  - `ChatResponseType.WORKFLOW`
  - `ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED` / `WORKFLOW_CANCELLED`
  - `HeadlessState.pending_workflow`
- `e2e/src/aica_client/client/e2e_client.py` の workflow 受信・検証・dispatch
  - `_validate_ws_event_contract()` への WORKFLOW branch 追加
  - `_validate_history_record()` の許容型拡張
  - `_update_state_from_exchange()` の WORKFLOW branch 追加
  - `_handle_workflow()` メソッド新規追加
  - `_handle_pending_actions()` への pending_workflow dispatch 追加
- `e2e/src/aica_client/client/e2e_client.py` の workflow 前提 contract drift 吸収
  - `positions/search_filter/current` など workflow 前に叩かれる REST payload の互換性差分を受理し、workflow verification を阻害しない状態にする

スコープ外:
- サーバー側の変更（サーバーは既に正しい）
- e2e 設定ファイル、persona 定義、LLM リポジトリの変更
- workflow 以外の既存 e2e ビジネスロジックのリファクタ
- server 側の unit test や contract test

## 開始条件

- Phase 4 が完了しており、`chat_service_refactored.ChatService` が legacy 委譲なしで実行されている。
- `e2e/` package の Pydantic `ChatStreamResponseModel.model_validate_json()` が `response_type="workflow"` を受理できない状態になっている（Phase 4 で `ToolEventHandler` が `WORKFLOW` event を emit するようになった）。

## 終了条件

- `ChatResponseType.WORKFLOW` が `e2e/src/aica_client/models.py` に存在する。
- `ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED` / `WORKFLOW_CANCELLED` が `e2e/src/aica_client/models.py` に存在する。
- `HeadlessState.pending_workflow` が存在し、WORKFLOW event 受信時に設定される。
- `_handle_workflow()` が `WORKFLOW_ANSWERS_SUBMITTED` payload を `_send_ws_action()` 経由で送信し、`workflow_received` / `workflow_submitting` / `workflow_handled` をログに記録する。
- `_validate_ws_event_contract()` が WORKFLOW payload の `"id"` フィールドを検証する。
- `_validate_history_record()` が WORKFLOW を許容型として含む。
- workflow verification 前の REST 初期化経路が既知 contract drift で停止しない。
- workflow 発火シナリオで e2e run が中断しない。
- workflow 非発火シナリオで既存挙動が退行しない。

## フィーチャー

| フィーチャー | 目的 | 依存関係 | ステータス |
| --- | --- | --- | --- |
| feature-1-e2e-model-contract | `models.py` の enum と state を workflow 対応に拡張する。 | Phase 4 完了 | done |
| feature-2-e2e-client-workflow-handling | `e2e_client.py` の受信・検証・dispatch・送信ロジックを追加する。 | feature-1 | blocked |
| feature-3-e2e-search-filter-contract-compatibility | workflow verification 前の REST 初期化経路にある search filter contract drift を吸収し、workflow path まで到達できるようにする。 | feature-2 task-2 blocker 確認 | blocked |

## タスク分割

| フィーチャー | タスク | 目的 | 必須検証 |
| --- | --- | --- | --- |
| feature-1-e2e-model-contract | task-1-enum-state-extension | `ChatResponseType.WORKFLOW`、workflow request types、`HeadlessState.pending_workflow` を追加する。 | static lint check; `model_validate_json` smoke check |
| feature-2-e2e-client-workflow-handling | task-1-contract-validation-updates | `_validate_ws_event_contract()` と `_validate_history_record()` を WORKFLOW 対応に更新する。 | static lint check |
| feature-2-e2e-client-workflow-handling | task-2-workflow-receive-dispatch-send | `_update_state_from_exchange()`、`_handle_workflow()`、`_handle_pending_actions()` を追加・更新する。 | static lint check; workflow 発火シナリオでの e2e 実行確認; 非発火シナリオ回帰確認 |
| feature-3-e2e-search-filter-contract-compatibility | task-1-other-filter-type-compatibility | `positions/search_filter/current` の `OtherFilters[].Type` drift を e2e contract が受理できるようにし、workflow verification blocker を除去する。 | static lint check; search filter current refresh の手動確認; workflow task の再実行 |
| feature-3-e2e-search-filter-contract-compatibility | task-2-contract-regression-tests | search filter drift と workflow receive/dispatch/send の互換性回帰を固定する focused test を追加する。 | `pytest` による追加テスト pass; static lint check |

## 必須検証

- `cd e2e && ../.venv-e2e/bin/python -m ruff check src/`
- workflow 発火シナリオを含む e2e run での確認（`./e2e/start_test.sh`）
- 既存シナリオでの回帰確認

## メモ

- e2e package には unit test が存在しないため（e2e 自体がテストハーネス）、verification は static check と実行確認で代替する。
- 変更はすべて additive であり、既存の `if/elif` チェーンへの分岐追加と新フィールド追加のみ。
- `_handle_workflow()` のデフォルトポリシーは常に submit（cancel しない）とし、`_handle_jobtype_search_result()` の先例に倣う。
- feature-2 の workflow verification が workflow 到達前の `positions/search_filter/current` contract mismatch で停止した場合、その drift 解消は feature-3 の責務とする。
- 2026-06-09 の user 判断により、この phase は Gate A completion scope の blocker としては扱わない（非 blocking）。残タスクは e2e client 側の追随作業として履歴を保持するが、phase-6 release readiness の完了判定は妨げない。
