# 引き継ぎ: task-2-turn-preparer

## 概要

`TurnPreparer` を `services/chat/turn_preparer.py` として抽出し、`ChatService` に組み込んだ。
あわせて `ConversationState` のブリッジガード（`mark_bridged` / `_bridged`）を削除し、
`_sync_state_from_legacy()` のコンテナ参照を alias から値コピーへ変更した。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat/turn_preparer.py` | 新規作成。`TurnPreparer` クラス（`prepare_turn`, `get_message_role`, `_get_position_detail`, `_find_last_non_position_guide_agent`, `_create_position_agent_if_not_exist`, `set_toolcall_trace_message`） |
| `server/src/aica_agent/services/chat_service_refactored.py` | `TurnPreparer` を DI。`_sync_state_from_legacy()` でコンテナを値コピーに変更。`chat()` で `_resolve_chat_key()` → `prepare_turn()` 呼び出しに変更。`get_message_role` を TurnPreparer 経由に変更。 |
| `server/src/aica_agent/services/chat/conversation_state.py` | `_bridged` フィールドと `mark_bridged()` メソッドを削除。`reset()` の RuntimeError ガードを削除。 |
| `server/tests/unit/services/chat/test_turn_preparer.py` | 新規作成。26 テスト、100% branch coverage。 |
| `server/tests/unit/services/chat/test_conversation_state.py` | bridge guard 関連テスト（2 件）を削除。 |
| `server/tests/unit/services/test_chat_service_refactored.py` | alias 前提のテストを値コピー前提に更新。`prepare_turn` モック対象を `legacy._prepare_for_chat_turn` から `_turn_preparer.prepare_turn` へ変更。 |
| `server/tests/integration/chat_service_contract/test_refactored_bootstrap_shell.py` | parity test の `inner._previous_response_ids` / `inner._conversation` アサーションを `chat_svc._conv_state.*` に変更（alias 廃止に対応）。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `TurnPreparer(position_service, chat_persistence, conv_state, agents)` — LLM ターン入力準備コンポーネント。
- `TurnPreparer.prepare_turn(request)` — `ConversationState.conversation / active_agent_name / chat_key / position_id` を更新する非同期メソッド。
- `TurnPreparer.get_message_role(request_type)` — `ChatRequestType` → `LLMMessageRole` 変換。
- `TurnPreparer.set_toolcall_trace_message(msg)` — `init_session()` 後に呼ばれるトレースメッセージ設定。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| コンテナを alias → 値コピーに変更 | TurnPreparer が `_conv_state` に直接書き込むため alias は不要。bridge guard も削除できる。 | alias を残して TurnPreparer がコピー後に呼ばれる方式 → 複雑性が増す |
| parity test の assertion を `_conv_state.*` に移動 | `inner._previous_response_ids` / `inner._conversation` は alias でなくなったため legacy に書き戻されない。`_conv_state` が唯一の権威として機能する。 | 書き戻し同期を追加 → 不要な複雑性 |
| `AgentName` は `services.llm_service` からインポート | `agents` パッケージには定義がない。 | `from agents import AgentName`（誤り — 修正済み） |

## 互換性メモ

- `ConversationState.mark_bridged()` は削除済み。呼び出し箇所は `chat_service_refactored.py` のみで、`_sync_state_from_legacy()` から削除した。
- `legacy._conversation` / `legacy._previous_response_ids` は chat ターン内では更新されなくなった。`legacy._active_agent_name` と `legacy._should_save` は引き続き同期している（non-chat public methods が参照するため）。
- `ConversationState` は純粋データコンテナのまま。外部 I/O なし。

## 次タスクへのフォローアップ

- `legacy._conversation` / `legacy._previous_response_ids` を参照している non-chat public methods（`summarize_position_detail_chat` など）が legacy 経由で動く限り問題ないが、phase-4 feature-4 以降で legacy 依存を外す際は注意が必要。
- `_resolve_chat_key()` は `chat_service_refactored.py` 内に inline で残っている。feature-4 で TurnPreparer に移動するか検討する。

## 未解決の質問

なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
