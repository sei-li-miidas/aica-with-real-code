# 引き継ぎ: replay contract and state-access cleanup

## 概要

`LLMRunStream` の replay 契約を `replay_items` に統一し、Completions replay の整形ロジックを強化した。あわせて refactored residual tests を `ConversationState` 直参照へ移行し、backcompat property 依存を削除した。

レビューで弾く条件:
- 変更ファイル、互換性メモ、次タスクへのフォローアップ、未解決の質問のいずれかが `未記入` のまま。
- replay 契約変更の影響範囲（runner/stream processor/tests）が追跡できない。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat/llm_runner.py` | `tool_replay_items` を `replay_items` へ統一し、Completions replay canonicalization と fake id 正規化を追加した。 |
| `server/src/aica_agent/services/chat/stream_event_processor.py` | run stream 参照を `replay_items` 契約へ追従させた。 |
| `server/src/aica_agent/services/chat/tool_event_handler.py` | replay item 名称統一と stop-at-tool 連携経路の整合を取った。 |
| `server/src/aica_agent/services/chat_service_refactored.py` | backcompat property 群を削除し、stop-at-tool append の unsafe fallback を廃止した。 |
| `server/src/aica_agent/services/chat/history_mapper.py` | `PositionKeyword` が null の場合に空文字へ正規化する境界処理を追加した。 |
| `server/tests/unit/services/chat/test_llm_runner.py` | replay 契約統一、Completions replay/id 正規化、continuation state のテストを拡張した。 |
| `server/tests/integration/chat_service_contract/test_refactored_residual_coverage.py` | `_state(...)` helper を使う `ConversationState` 直参照検証へ移行した。 |
| `server/tests/integration/chat_service_contract/test_runner_contract.py` ほか contract/residual tests | `replay_items` 契約へ追従し、fixture 名称も一致させた。 |

## 互換性メモ

- Responses 経路は `replay_items` naming 以外の public behavior を変えず、runner contract test で既存整合を維持した。
- Completions 経路は replay item の canonicalization を追加したが、tool call/output の対を維持する方向の tightening であり、履歴の保存フォーマットには影響しない。
- `chat_service_refactored.py` で ToolEventHandler 不在時 fallback append を無効化したため、該当経路は安全側 noop + error log へ変わる。

## 次タスクへのフォローアップ

- feature-3 parity-and-rollback では `replay_items` 契約変更後の responses/completions parity を明示的に比較すること。
- stop-at-tool replay fixture を増やす場合は、孤立 output を replay に混ぜない canonicalization 前提で作成すること。
- residual coverage 拡張時は backcompat property の再導入ではなく `ConversationState` 直参照を維持すること。

## 未解決の質問

- なし。feature-2 scope の replay/state-access 整理は local diff 範囲で完了。