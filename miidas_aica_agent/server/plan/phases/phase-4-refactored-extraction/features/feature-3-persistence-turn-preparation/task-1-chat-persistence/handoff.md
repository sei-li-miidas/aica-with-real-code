# 引き継ぎ: task-1-chat-persistence

## 概要

`ChatPersistence` コンポーネントを新規作成し、`chat_service_refactored.ChatService` に組み込んだ。
DB 副作用テストに real-refactored バリアントを追加し、gate_a_scenario_matrix.md を更新した。

`ConversationState` の `mark_bridged()` / `_bridged` ブリッジガードは **残存している**。
`_sync_state_from_legacy()` がミュータブルコンテナを legacy と alias した後に `mark_bridged()` を呼ぶことで、
alias 期間中の `reset()` による alias 破壊を防ぐ。このガードは task-2-turn-preparer で TurnPreparer
を抽出した時点で削除する。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat/chat_persistence.py` | 新規作成: セッション作成・履歴保存・ツール出力更新・遅延保存キュー管理 |
| `server/src/aica_agent/services/chat_service_refactored.py` | ChatPersistence を組み込み、`_sync_state_from_legacy()` 末尾で `mark_bridged()` を呼ぶ |
| `server/src/aica_agent/services/chat/conversation_state.py` | `conversation` の初期値を `{MAIN_CHAT_KEY: []}` に統一（`chat_histories` との整合）。`mark_bridged()` / `_bridged` は継続保持 |
| `server/tests/unit/services/chat/test_chat_persistence.py` | 新規作成: ChatPersistence ユニットテスト (100% branch coverage) |
| `server/tests/unit/services/chat/test_conversation_state.py` | `test_mark_bridged_prevents_reset` / `test_reset_before_mark_bridged_succeeds` を追加、`conversation` 初期値アサートを更新 |
| `server/tests/unit/services/test_chat_service_refactored.py` | bridge test を alias 動作テストに更新 |
| `server/tests/integration/chat_service_contract/conftest.py` | `chat_service_container_db_side_effects` fixture 追加、`_resolve_variant()` ヘルパー導入（`getfixturevalue` → `callspec.params` 修正） |
| `server/tests/integration/chat_service_contract/chat_service_contract_helpers.py` | `_FakeRunStream` 追加 |
| `server/tests/integration/chat_service_contract/test_db_side_effects.py` | real-refactored バリアントを有効化、retry テストは legacy/delegating のみ |
| `server/plan/phases/gate_a_scenario_matrix.md` | DB side effects を pass に更新 |
| `server/plan/phases/status.md` | task-1 を done に更新 |

## 新しい API / ヘルパー / フィクスチャ

### `ChatPersistence` (services/chat/chat_persistence.py)

```python
class ChatPersistence:
    def __init__(self, chat_repository: ChatRepository, conv_state: ConversationState) -> None: ...
    def set_toolcall_trace_content(self, content: str) -> None: ...
    def save_chat_history(self, item: RunItem) -> None: ...
    def create_session(self, session_status: ChatSessionStatus) -> None: ...
    def save_user_or_developer_message(self, request: ChatRequestModel) -> None: ...
    def save_llm_error(self, message_to_llm: str) -> None: ...
    def save_chat_histories(self, chat_histories: list[ChatHistory]) -> None: ...
```

### `_FakeRunStream` (chat_service_contract_helpers.py)

real-refactored バリアントのコントラクトテストで `LLMRunner.run_streamed` の戻り値として使用する。

### `chat_service_container_db_side_effects` fixture (conftest.py)

DB 副作用テスト専用の全 3 variant (legacy / delegating-refactored / real-refactored) を解決する fixture。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| `ChatPersistence` は `ConversationState` を参照として受け取る | DI 境界を `ChatRepository` のみに保ち、state container は参照渡しで副作用を conv_state に書き戻す | state を引数で渡す（都度渡しは多数のメソッドで冗長） |
| `_deferred_queue` を `ChatPersistence` に持つ | should_save=False 中の RunItem / ChatRequestModel / ChatHistory を溜め置く責務は ChatPersistence に集約 | ChatService が持つ（単一責務の観点で不適切） |
| ブリッジ期間中もコンテナを alias で保持 | `_prepare_for_chat_turn` は legacy.* を直接変更するため、TurnPreparer 抽出 (task-2) までは alias が必要 | 毎ターン後にコンテナを deep copy する（コスト高・複雑） |
| `mark_bridged()` / `_bridged` を継続保持 | alias 期間中に `reset()` が呼ばれると legacy と _conv_state が黙って乖離する。`RuntimeError` ガードによりコードで不変条件を強制する。task-2 で TurnPreparer 抽出後に削除する | ガードを削除し docstring のみで説明する（コード上の不変条件保証なし） |
| `test_db_retry_error_save` は legacy/delegating のみ | real-refactored はリトライループを持たないため、同一シナリオを real-refactored で検証することは不可能 | real-refactored 向けの別シナリオを追加する（task-2 以降の課題） |
| `legacy._session_created` を create_session 後に同期 | `_sync_scalars_from_legacy()` が次ターン開始時に上書きするため、直後に明示的に同期が必要 | `_sync_scalars_from_legacy()` を session_created にも対応させる（現時点では不要） |

## 互換性メモ

- `ConversationState.reset()` は `_bridged=True` 中は `RuntimeError` を送出する。
  `mark_bridged()` は `_sync_state_from_legacy()` の末尾で呼ばれるため、
  `init_session()` 完了後は `reset()` を呼べない。task-2 で TurnPreparer を抽出したら削除する。
- `_sync_state_from_legacy()` (init_session 後に 1 回呼ぶ) と
  `_sync_scalars_from_legacy()` (prepare_for_chat_turn 後に呼ぶ) の 2 メソッドが残る。
  いずれも task-2 で TurnPreparer 抽出後に削除する。
- legacy の `_save_chat_history` / `_create_session` / `_save_user_or_developer_message` は
  legacy.chat() パスでは引き続き使用されている（delegating モード）。
  real-refactored パスでは `_chat_persistence.*` を使用する。

## 次タスク (task-2-turn-preparer) へのフォローアップ

- `legacy._prepare_for_chat_turn` を `TurnPreparer` として抽出したら、
  `_sync_scalars_from_legacy()` と container alias が不要になる。
- その時点で `_conv_state` が唯一の状態保持者となり、`legacy.*` へのフォールバックがすべて削除できる。
- `chat_service_container_db_side_effects` / `chat_service_container_history_parity` の
  fixture が `chat_service_container` と統合できる（pending-phase-4 skip 除去は feature-4）。

## 未解決の質問

- `_save_llm_error` は real-refactored パスでは呼ばれないが、feature-4 でリトライループを
  追加する際に `ChatPersistence.save_llm_error()` を使うべきか？ → feature-4 で判断する。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
