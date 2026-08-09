# 引き継ぎ: task-2-responses-runner-adapter

## 概要

`services/chat/llm_runner.py` を追加し、Responses style の runner contract を `LLMRunStream` / `LLMRunner` で固定した。SDK-shaped fixture から normalized event への変換、`previous_response_id` の forwarding、`tool_replay_items` と `usage` の読み取りを contract test で固定している。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat/llm_runner.py` | `LLMRawResponseEvent` / `LLMRunItemStreamEvent` / `LLMRunStream` / `LLMRunner` / `ResponsesRunStream` / `ResponsesAgentRunner` を追加した。 |
| `server/tests/integration/chat_service_contract/test_runner_contract.py` | SDK-shaped fixture の normalized contract と Responses adapter forwarding を検証するテストを追加した。 |
| `server/plan/phases/phase-3-runner-contract-pre-extraction/README.md` | feature-1 ステータスを `done` に更新した。 |
| `server/plan/phases/phase-3-runner-contract-pre-extraction/features/feature-1-responses-runner-contract/README.md` | task-2 ステータスを `done` に更新した。 |
| `server/plan/phases/status.md` | phase 3 の task-2 ステータスを `done` に更新した。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `LLMRawResponseEvent`
- `LLMRunItemStreamEvent`
- `LLMRunStream`
- `LLMRunner`
- `ResponsesRunStream`
- `ResponsesAgentRunner`

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| Responses adapter は legacy production path へまだ差し込まない | Phase 3 の目的は runner contract を固定することであり、production path の normalized stream 消費は Phase 4 の refactored shell に寄せるため。 | legacy `ChatService._run_streamed()` を即座に `LLMRunStream` へ置き換える。 |
| normalized contract は `LLMRunStream` へ閉じ、Responses compatibility field を外へ出さない | `previous_response_id` / `last_response_id` / `last_agent` / `to_input_list()` を Phase 3 の stable contract に混ぜないため。 | これらの field を public contract としてそのまま露出する。 |

## 互換性メモ

- 既存の `services.chat_service.ChatService._run_streamed()` seam はそのまま維持した。
- 新しい adapter は contract test でのみ利用し、legacy stream consumption の observable behavior は変更していない。

## 次タスクへのフォローアップ

- Phase 4 以降は `ResponsesRunStream` を `chat_service_refactored.ChatService` 側から消費する前提で、`stream_events()`, `continuation_state`, `agent_state`, `tool_replay_items`, `usage` を stable contract として扱える。
- `ResponsesAgentRunner` は `Runner.run_streamed(..., previous_response_id=...)` の thin wrapper として再利用できる。

## 未解決の質問

- なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
