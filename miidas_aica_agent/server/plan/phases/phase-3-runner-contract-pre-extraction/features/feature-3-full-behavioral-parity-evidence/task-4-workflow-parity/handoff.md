# 引き継ぎ: task-4-workflow-parity

## 概要

`test_workflow_side_effects.py` の `fixture-schema only` テストを完全な behavioral runtime assertions に置き換えた。
jobtype selected/clear と workflow submitted/cancelled の 4 シナリオについて、legacy /
delegating-refactored 両 variant で public workflow entrypoint を実行し、state mutation と
chat stream contract を runtime で検証する。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/tests/integration/chat_service_contract/test_workflow_side_effects.py` | schema-only テスト 4 本を async behavioral テスト 4 本に置換。jobtype selected/clear と workflow submitted/cancelled の副作用、persisted history、stream contract を検証する。 |
| `server/tests/integration/chat_service_contract/fixtures/workflow_side_effects.json` | 各シナリオの request payload、expected state change、persisted history pair、stream contract key/type を追加。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | `workflow side effects` の `legacy evidence` を `fixture-schema only` から `pass` に更新。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `_make_text_delta(item_id, delta)`: `ResponseTextDeltaEvent` を持つ `raw_response_event` を作る test-local helper。
- `_make_workflow_definition(workflow_id, workflow_name)`: `WorkflowService` を real のまま使うための最小 `WorkflowDefinition` real instance。
- `_collect_responses(generator)`: workflow 系 public method が返す async generator を消費し、`ChatStreamResponseModel` の deep copy を収集する helper。
- `_assert_stream_contract(responses, request_type, stream_contract)`: 全 response の key/request_type を検証し、END 前がすべて MESSAGE であることと、chunk を再結合した assistant message が fixture と一致することを確認する helper。
- `workflow_session_id` fixture: test ごとに UUID 付き session id を発行し、teardown で `clear_session_id()` を実行する。
- `workflow_side_effects.json`: jobtype selected/clear と workflow submitted/cancelled の入力、期待副作用、stream contract を source of truth として保持する。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| workflow 系 entrypoint は `chat()` に戻る現行 public behavior をそのままテストする | task の目的は behavioral parity であり、実装を理想化した nonexistent API に合わせないため | `workflow_cancelled()` に未実装の cancel repository write を期待する（false negative になる） |
| `WorkflowService` は real instance を使い、definition/repository だけをモックする | feature README の boundary 方針に従い、in-process の business logic は runtime で通すため | `WorkflowService` 自体をモックして unit test 化する |
| stream contract は chunk 単位 MESSAGE + final END として検証する | `chat()` は delta を chunk ごとに yield するため、単一 MESSAGE を前提にすると false failure / false green のどちらも起こしやすい | MESSAGE 1 件だけを期待する |
| workflow submitted は `wf_{workflow_id}_*` 履歴の role/content pair を固定する | question/answer の role が入れ替わる regression を content-only アサートでは捕捉できないため | content 順序だけ確認する |

## 互換性メモ

- production code の変更はない。今回の差分は integration fixture と parity assertion 強化のみ。
- `real-refactored` variant は引き続き `pending-phase-4` skip。
- `workflow_cancelled()` の現行 behavior は workflow definition の存在確認のみで、workflow answer repository への cancel write は行わない。Phase 4 以降も public behavior の source of truth は現行実装とする。

## カバレッジ状況

コマンド: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ --cov=services.chat_service --cov-branch --cov-report=term-missing`

| 計測対象 | Stmts | Miss | Branch | BrPart | Coverage |
| --- | --- | --- | --- | --- | --- |
| このタスクのテストのみ | 787 | 502 | 348 | 50 | 31% |
| `pre_extraction_parity` スイート全体 | 787 | 337 | 348 | 77 | 52% |

このタスクで新たにカバーされた主要パス:
- `job_type_decided()` 正常パス: jobtype API 更新、LLM tool update、developer history 保存、`chat()` への委譲。
- `clear_jobtype()` 正常パス: clear API 呼び出し、tool reset、developer history 保存、`chat()` への委譲。
- `workflow_submitted()` 正常パス: `WorkflowService.process_workflow_submission()`、`save_workflow_answer()`、workflow question/answer history 保存、developer summary message。
- `workflow_cancelled()` 正常パス: known workflow definition lookup、developer cancellation message、`chat()` への委譲。

未カバーのパス:
- summary rollback は task-5 scope。
- residual branch closure は task-6〜7 scope。

`chat_service.py` branch coverage: task-4 完了時点で 52%。残りは task-5〜7 がカバーする。

## レビュー / 修正ログ

| pass | reviewer | 結果 | 指摘 | 対応 |
| --- | --- | --- | --- | --- |
| 1 | `code-reviewer` subagent | request-changes | stream contract helper が一部 false green を許す、workflow submitted が persisted role を見ていない、doc artifacts 未更新 | 全 response を検証する `_assert_stream_contract()` に修正、`saved_history_pairs` で role/content pair を固定、不要 fixture field を削除、task docs/matrix/status を更新 |
| 2 | `code-reviewer` subagent | clean | changed test/fixture files に追加指摘なし。stream contract helper、persisted role assertion、fixture scope が適切と確認 | 追加修正なし |

## 次タスクへのフォローアップ

- task-5 は `rollback_summary` を追加で埋めるが、`workflow side effects` の `legacy evidence` は今回の `test_workflow_side_effects.py` を source of truth にしてよい。
- Phase 4 完了後、`real-refactored` variant の skip を解除して同じ workflow parity assertions を real implementation に適用する。

## 未解決の質問

- なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
