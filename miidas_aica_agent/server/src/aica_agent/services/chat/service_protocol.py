from collections.abc import AsyncGenerator
from typing import Protocol, runtime_checkable

from domain.entities.chat_session import ChatSessionStatus
from utils.chat_request import ChatRequestModel
from utils.chat_response import ChatStreamResponseModel


@runtime_checkable
class ChatServiceProtocol(Protocol):
    async def check_if_previous_chat_histories_exist(
        self, encrypted_position_id: str
    ) -> bool:
        """指定ポジションに過去のチャット履歴があるかを返す。"""
        ...

    async def load_previous_chat_histories(
        self,
        limit: int,
        encrypted_position_id: str | None,
        before_id: str | None,
    ) -> tuple[list[dict], bool]:
        """指定位置より前の履歴を取得し、続きが残っているかも返す。"""
        ...

    async def init_session(
        self,
        model_name: str,
    ) -> tuple[ChatSessionStatus, bool]:
        """WebSocket セッションに紐づく chat state を初期化する。"""
        ...

    async def chat(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """通常のチャット入力を受け取り、ストリーム応答を返す。"""
        ...

    async def summarize_position_detail_chat(
        self,
        chat_request: ChatRequestModel,
    ) -> ChatSessionStatus:
        """求人詳細チャットの要約を実行し、次のセッション状態を返す。"""
        ...

    async def job_type_decided(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """職種選択後のフローを処理し、ストリーム応答を返す。"""
        ...

    async def clear_jobtype(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """職種選択を解除した際のフローを処理し、ストリーム応答を返す。"""
        ...

    async def workflow_submitted(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """応募フロー送信後の処理を行い、ストリーム応答を返す。"""
        ...

    async def workflow_cancelled(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """応募フローキャンセル時の処理を行い、ストリーム応答を返す。"""
        ...

    def get_initial_menu_response(self) -> ChatStreamResponseModel:
        """LLM を介さず初期メニューワークフロー定義を直接返す。"""
        ...
