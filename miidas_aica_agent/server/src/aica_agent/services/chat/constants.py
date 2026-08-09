"""chat サービス共通定数。"""

from __future__ import annotations

from utils.chat_request import ChatRequestType

# ユーザー・デベロッパーロールに対応するリクエストタイプ（LLMMessageRole.DEVELOPER を返す）
DEVELOPER_REQUEST_TYPES: frozenset[ChatRequestType] = frozenset(
    [
        ChatRequestType.START,
        ChatRequestType.RESTART_CHAT,
        ChatRequestType.JOB_TYPES_SELECTED,
        ChatRequestType.JOB_TYPES_CLEAR,
        ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
        ChatRequestType.WORKFLOW_CANCELLED,
    ]
)
