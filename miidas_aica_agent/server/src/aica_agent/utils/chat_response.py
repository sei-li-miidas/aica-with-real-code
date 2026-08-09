"""
チャット通信用のWebSocketレスポンスモデルとユーティリティを定義します。
"""

from enum import StrEnum
import json
import uuid
from pydantic import BaseModel

from domain.entities.chat_session import ChatSessionStatus
from utils.chat_request import ChatRequestType
from utils.enum import LLMMessageRole
from utils.log_utils import get_session_id


class ChatResponseType(StrEnum):
    """
    チャットレスポンスタイプ
    """

    MESSAGE = "message"
    POSITION_SEARCH_RESULT = "position_search_result"
    POSITION_SEARCH_LINK = "position_search_link"
    JOBTYPE_SEARCH_RESULT = "jobtype_search_result"
    WORKFLOW = "workflow"
    RESTART_WORKFLOW = "restart_workflow"
    ERROR = "error"
    END = "end"


class ChatStreamResponseModel(BaseModel):
    """
    チャットストリームレスポンスのPydanticモデル。

    Attributes:
        session_id: チャットセッションID。
        session_status: チャットセッションの現在のステータス。
        request_type: このレスポンスをトリガーした元のリクエストのタイプ。
        response_type: このレスポンスのタイプ（メッセージ、エラー、終了など）。
        role: LLMロール。
        message_id: メッセージID。
        message: レスポンス内容。
        position_id: ポジション詳細チャットの場合のポジションID。メインチャットの場合不要
        is_maintenance: システムがメンテナンスモードかどうかを示すフラグ。
    """

    session_id: str
    session_status: int
    request_type: ChatRequestType | None
    response_type: ChatResponseType
    role: LLMMessageRole | None = None
    message_id: str
    message: str
    position_id: str | None = None
    is_maintenance: bool


class ChatStreamResponse:
    """
    チャットストリームレスポンスの作成と管理。

    Attributes:
        _model: レスポンスモデル。
    """

    def __init__(
        self,
        request_type: ChatRequestType | None = None,
        position_id: str | None = None,
        session_status: ChatSessionStatus = ChatSessionStatus.CHATTING,
    ):
        """
        新しいChatStreamResponseインスタンスを初期化します。

        Args:
            request_type: レスポンスするチャットリクエストのタイプ。
            position_id: ポジション詳細チャットの場合のポジションID。メインチャットの場合不要
            session_status: チャットセッションの現在のステータス。
        """
        self._model = ChatStreamResponseModel(
            session_id=get_session_id(),
            session_status=session_status,
            request_type=request_type,
            response_type=ChatResponseType.MESSAGE,
            role=LLMMessageRole.ASSISTANT,
            message_id="",
            message="",
            position_id=position_id,
            is_maintenance=False,
        )

    def clone(self):
        """
        このChatStreamResponseのクローンを作成します。

        Returns:
            ChatStreamResponse: このインスタンスのクローン。
        """
        cloned = ChatStreamResponse(
            request_type=self._model.request_type,
            position_id=self._model.position_id,
            session_status=self._model.session_status,
        )
        cloned._model = self._model.model_copy(deep=True)
        return cloned

    def create_end_response(
        self,
        session_status: int = ChatSessionStatus.CHATTING,
    ) -> ChatStreamResponseModel:
        """
        チャット終了レスポンスを作成します。

        Args:
            session_status: チャットセッションの現在のステータス。

        Returns:
            ChatStreamResponseModel: チャット終了レスポンス。
        """
        return self.create_response(
            response_type=ChatResponseType.END,
            session_status=session_status,
        )

    def create_tool_result_response(
        self,
        message_id: str,
        response_type: ChatResponseType,
        result: dict,
        session_status: int = ChatSessionStatus.CHATTING,
    ) -> ChatStreamResponseModel:
        """
        ツール実行結果レスポンスを作成します。

        Args:
            message_id: メッセージID。
            response_type: ツール実行結果のレスポンスタイプ。
            result: ツール実行結果。
            session_status: チャットセッションの現在のステータス。

        Returns:
            ChatStreamResponseModel: ツール実行結果レスポンス。
        """
        return self.create_response(
            response_type=response_type,
            message=json.dumps(result),
            message_id=message_id,
            session_status=session_status,
        )

    def create_tool_result_link_response(
        self,
        message_id: str,
        position_search_conditions: dict,
        session_status: int = ChatSessionStatus.CHATTING,
    ) -> ChatStreamResponseModel:
        """
        検索結果を再取得するためのレスポンスを作成します。

        過去履歴を取得する際に、このメソッドは以前のキャッシュされた
        結果を使用する代わりに、新しい検索結果を促すレスポンスを作成します。

        Args:
            message_id: メッセージID。
            position_search_conditions: ポジション検索条件。
            session_status: チャットセッションの現在のステータス。

        Returns:
            ChatStreamResponseModel: 新しい検索結果を取得すべきことを示すレスポンス。
        """
        return self.create_response(
            response_type=ChatResponseType.POSITION_SEARCH_LINK,
            message=json.dumps(position_search_conditions),
            message_id=message_id,
            session_status=session_status,
        )

    def create_user_message_response(
        self,
        message_id: str,
        message: str,
        session_status: int = ChatSessionStatus.CHATTING,
    ) -> ChatStreamResponseModel:
        """
        ユーザーメッセージレスポンスを作成します。

        Args:
            message: ユーザーのメッセージ内容。
            session_status: チャットセッションの現在のステータス。

        Returns:
            ChatStreamResponseModel: ユーザーのメッセージレスポンス。
        """
        return self.create_response(
            response_type=ChatResponseType.MESSAGE,
            role=LLMMessageRole.USER,
            message=message,
            message_id=message_id,
            session_status=session_status,
        )

    def create_agent_message_response(
        self,
        message_id: str,
        message: str,
        session_status: int = ChatSessionStatus.CHATTING,
    ) -> ChatStreamResponseModel:
        """
        AIエージェントメッセージレスポンスを作成します。

        Args:
            message_id: メッセージID。
            message: AIエージェントのレスポンスメッセージ。
            session_status: チャットセッションの現在のステータス。

        Returns:
            ChatStreamResponseModel: AIエージェントのメッセージレスポンス。
        """
        return self.create_response(
            response_type=ChatResponseType.MESSAGE,
            message=message,
            message_id=message_id,
            session_status=session_status,
        )

    def create_error_response(
        self,
        error: str,
        session_status: int = ChatSessionStatus.CHATTING,
        is_maintenance: bool = False,
    ) -> ChatStreamResponseModel:
        """
        例外が発生した場合のエラーレスポンスを作成します。

        Args:
            error: エラーメッセージ。
            session_status: チャットセッションの現在のステータス。
            is_maintenance: エラーがメンテナンスモードによるものかどうか。

        Returns:
            ChatStreamResponseModel: エラーメッセージレスポンス。
        """
        return self.create_response(
            response_type=ChatResponseType.ERROR,
            message=error,
            session_status=session_status,
            is_maintenance=is_maintenance,
        )

    def create_token_usage_response(
        self,
        token_usage: str,
        session_status: int = ChatSessionStatus.CHATTING,
    ) -> ChatStreamResponseModel:
        """
        トークン使用量レスポンスを作成します。

        Args:
            token_usage: トークン使用量情報。
            session_status: チャットセッションの現在のステータス。

        Returns:
            ChatStreamResponseModel: トークン使用量レスポンス。
        """
        return self.create_response(
            response_type=ChatResponseType.MESSAGE,
            role=LLMMessageRole.ASSISTANT,
            message=token_usage,
            session_status=session_status,
        )

    def create_response(
        self,
        response_type: ChatResponseType,
        message: str = "",
        role: LLMMessageRole = LLMMessageRole.ASSISTANT,
        message_id: str | None = None,
        session_status: int = ChatSessionStatus.CHATTING,
        is_maintenance: bool = False,
    ) -> ChatStreamResponseModel:
        """
        クライアントに送信する汎用レスポンスを作成します。

        Args:
            response_type: 作成されるレスポンスのタイプ。
            message: レスポンスメッセージの内容。
            role: LLMロール。
            message_id: メッセージID。提供されない場合は生成されます。
            session_status: チャットセッションの現在のステータス。
            is_maintenance: システムがメンテナンスモードかどうか。

        Returns:
            ChatStreamResponseModel: クライアントに送信するレスポンスモデル。
        """
        self._model.session_status = session_status
        self._model.response_type = response_type
        self._model.role = role
        self._model.message_id = message_id if message_id else str(uuid.uuid4())
        self._model.message = message
        self._model.is_maintenance = is_maintenance
        return self._model
