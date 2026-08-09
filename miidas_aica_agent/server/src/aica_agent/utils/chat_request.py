from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from utils.enum import PageName


class ChatRequestType(StrEnum):
    # 会話開始
    START = "start"
    # チャット
    CHAT = "chat"
    # 過去チャット再開
    RESTART_CHAT = "restart_chat"
    # ポジション詳細チャットまとめ
    SUMMARIZE_POSITION = "summarize_position"
    # 職種決定
    JOB_TYPES_SELECTED = "job_types_selected"
    # 職種検討し直し
    JOB_TYPES_CLEAR = "job_types_clear"
    # ワークフロー回答
    WORKFLOW_ANSWERS_SUBMITTED = "workflow_answers_submitted"
    # ワークフロー中断
    WORKFLOW_CANCELLED = "workflow_cancelled"


class ChatRequestModel(BaseModel):
    request_type: ChatRequestType = ChatRequestType.CHAT
    current_page: PageName
    previous_page: PageName | None = None
    message: Annotated[str | None, StringConstraints(strip_whitespace=True)] = None
    position_id: str | None = None
    current_message_id: str | None = None
    is_voice: bool | None = None
