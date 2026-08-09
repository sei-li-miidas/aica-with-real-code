"""WebSocket チャットフローのセッション単位ミュータブル状態コンテナ。

ConversationState は 1 つの WebSocket/セッションライフサイクルに属するミュータブルな
セッション変数のみを保持する。外部 I/O・ビジネスロジック・外部依存は一切持たない。
状態更新の判断はオーケストレーターである ChatService が行い、ConversationState は
純粋なデータコンテナである。

ライフサイクル
--------------
* ChatService インスタンス（WebSocket 接続ごとにファクトリスコープで生成）につき
  1 つの ConversationState インスタンスが作られる。
"""

from __future__ import annotations

from typing import Any

from utils.const import MAIN_CHAT_KEY


class ConversationState:
    """WebSocket チャットフローのセッション単位ミュータブル状態を保持する。

    各フィールドは LegacyChatService.__init__ / init_session() に散在していた
    プライベートインスタンス変数と 1 対 1 で対応する。

    +-----------------------------------------+-------------------------------+
    | ConversationState フィールド            | Legacy ChatService フィールド  |
    +-----------------------------------------+-------------------------------+
    | model_name                              | _provider  (※名称に反しモデル名を保持)|
    | active_agent_name                       | _active_agent_name            |
    | chat_key                                | _chat_key                     |
    | position_id                             | _position_id                  |
    | previous_continuation_states             | _previous_response_ids        |
    | conversation                            | _conversation                 |
    | chat_histories                          | _chat_histories               |
    +-----------------------------------------+-------------------------------+
    """

    def __init__(self) -> None:
        self.model_name: str = ""
        self.active_agent_name: str = ""
        self.chat_key: str = MAIN_CHAT_KEY
        self.position_id: str | None = None
        self.previous_continuation_states: dict[str, Any] = {}
        self.conversation: dict[str, list[Any]] = {MAIN_CHAT_KEY: []}
        self.chat_histories: dict[str, list[Any]] = {MAIN_CHAT_KEY: []}
