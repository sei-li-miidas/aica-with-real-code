# 引き継ぎ: task-1-legacy-runner-seam-and-fixtures

## 概要

legacy `ChatService` に `_run_streamed()` seam を追加し、runner contract 用の SDK-shaped fixtures と `rollback_runner` テスト scaffold を実体化した。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat_service.py` | `Runner.run_streamed(...)` を包む `_run_streamed()` seam を追加し、`chat()` からそこを呼ぶようにした。 |
| `server/tests/integration/chat_service_contract/test_runner_contract.py` | runner contract の seam / fixture shape / replay payload / usage payload を確認するテストを追加した。 |
| `server/tests/integration/chat_service_contract/fixtures/sdk_stream_events.py` | SDK-shaped stream event fixture と `FakeRunResult` を追加した。 |
| `server/tests/integration/chat_service_contract/fixtures/stop_at_tool_replay.json` | function call output replay fixture を追加した。 |
| `server/tests/integration/chat_service_contract/fixtures/usage_response.json` | runner usage fixture を追加した。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | runner event normalization / stop-at-tool replay / usage propagation の legacy evidence を scaffold test に紐づけた。 |
| `server/plan/phases/phase-3-runner-contract-pre-extraction/README.md` | feature-1 のステータスを `in-progress` に更新した。 |
| `server/plan/phases/phase-3-runner-contract-pre-extraction/features/feature-1-responses-runner-contract/README.md` | task-1 のステータスを `done` に更新した。 |
| `server/plan/phases/status.md` | phase 3 進捗と task-1 完了を反映した。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `ChatService._run_streamed(starting_agent, input, previous_response_id)`
- `tests/integration/chat_service_contract/fixtures/sdk_stream_events.py`
- `tests/integration/chat_service_contract/fixtures/stop_at_tool_replay.json`
- `tests/integration/chat_service_contract/fixtures/usage_response.json`
- `FakeRunResult.stream_events()`
- `FakeRunResult.to_input_list()`

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| legacy runner seam は private method に閉じる | task 1 の目的は runner 呼び出しの差し込み口だけを作ることで、public contract を増やさないため。 | constructor injection で runner 依存を公開する。 |
| fixtures は Python と JSON を分ける | SDK-shaped event は Python の object graph で扱う方が自然で、replay/usage は data fixture として独立させた方が次 task で扱いやすいため。 | すべて Python fixture に寄せる。 |

## 互換性メモ

- `chat()` の observable behavior は変更していない。runner 呼び出しを private seam で包んだだけ。
- fixture 追加は contract test 専用で、production code の依存は増やしていない。

## 次タスクへのフォローアップ

- task 2 は `_run_streamed()` seam を利用して Responses adapter / normalized contract を固定できる。
- `sdk_stream_events.py` の `FakeRunResult` は task 2 以降の stream normalization / replay テストに再利用できる。
- `gate_a_scenario_matrix.md` の `real-refactored evidence` はまだ `pending-phase-4` のままにしているので、task 2 で legacy/delegating characterization を上書きしないこと。

## 未解決の質問

- なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
