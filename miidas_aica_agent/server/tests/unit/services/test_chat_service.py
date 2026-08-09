"""
ChatServiceのチャット履歴関連メソッドの単体テスト。
"""

import json
from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock, patch
from types import SimpleNamespace
from uuid import UUID

import pytest

from agents import Agent
from domain.entities.chat_history import ChatHistory
from domain.entities.chat_session import ChatSessionStatus
from repositories.chat_repo import ChatRepository
from repositories.position_repo import PositionRepository
from repositories.user_repo import UserRepository
from repositories.action_log_repo import ActionLogRepository
from services.chat_service import ChatService, ToolName
from services.workflow_handlers.base import WorkflowPostProcessingResult
from services.llm_service import AgentName, LLMService
from services.conversation_summary_service import ConversationSummaryService
from services.position_service import PositionService
from services.rate_limit_service import RateLimitService
from utils.chat_response import ChatResponseType, ChatStreamResponse
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.const import MAIN_CHAT_KEY, SESSION_START_MESSAGE
from utils.enum import LLMMessageRole, LocationType, PageName
from utils.log_utils import set_session_id, clear_session_id


@pytest.fixture(autouse=True)
def session_scope():
    """全テストでセッションIDをセットアップする。"""
    set_session_id("test-session-id")
    yield
    clear_session_id()


@pytest.fixture(autouse=True)
def mock_retry_sleep(monkeypatch):
    """Prevent the retry loop's exponential backoff from sleeping for real.

    chat_service.py retries up to MAX_LLM_RETRY_COUNT=5 times with asyncio.sleep
    delays and also calls asyncio.sleep(0.001) per streaming chunk. Without this
    fixture, error-path tests would block for 7.5s of real wall-clock time.
    """
    monkeypatch.setattr("services.chat_service.asyncio.sleep", AsyncMock())


@pytest.fixture
def mock_chat_repo():
    """ChatRepositoryのモックを作成する。"""
    return Mock(spec=ChatRepository)


@pytest.fixture
def mock_position_svc():
    """PositionServiceのモックを作成する。"""
    return Mock(spec=PositionService)


@pytest.fixture
def mock_llm_svc():
    """LLMServiceのモックを作成する。"""
    return Mock(spec=LLMService)


@pytest.fixture
def mock_conversation_summary_svc():
    """ConversationSummaryServiceのモックを作成する。"""
    return Mock(spec=ConversationSummaryService)


@pytest.fixture
def mock_position_repo():
    """PositionRepositoryのモックを作成する。"""
    return Mock(spec=PositionRepository)


@pytest.fixture
def mock_user_repo():
    """UserRepositoryのモックを作成する。"""
    return Mock(spec=UserRepository)


@pytest.fixture
def mock_action_log_repo():
    """ActionLogRepositoryのモックを作成する。"""
    return Mock(spec=ActionLogRepository)


@pytest.fixture
def mock_rate_limit_svc():
    """RateLimitServiceのモックを作成する。"""
    return Mock(spec=RateLimitService)


@pytest.fixture
def mock_workflow_svc():
    """WorkflowServiceのモックを作成する。"""
    return AsyncMock()


@pytest.fixture
def chat_service(
    mock_position_svc,
    mock_llm_svc,
    mock_chat_repo,
    mock_position_repo,
    mock_user_repo,
    mock_action_log_repo,
    mock_rate_limit_svc,
    mock_workflow_svc,
    mock_conversation_summary_svc,
):
    """モック依存を使ってChatServiceを作成する。"""
    return ChatService(
        position_svc=mock_position_svc,
        llm_svc=mock_llm_svc,
        chat_repository=mock_chat_repo,
        position_repository=mock_position_repo,
        user_repository=mock_user_repo,
        action_log_repository=mock_action_log_repo,
        rate_limit_service=mock_rate_limit_svc,
        workflow_service=mock_workflow_svc,
        conversation_summary_svc=mock_conversation_summary_svc,
    )


class TestGetMessageRole:
    @pytest.mark.parametrize(
        "request_type",
        [
            ChatRequestType.START,
            ChatRequestType.RESTART_CHAT,
            ChatRequestType.JOB_TYPES_SELECTED,
            ChatRequestType.JOB_TYPES_CLEAR,
        ],
    )
    def test_returns_developer_for_control_requests(self, chat_service, request_type):
        assert chat_service._get_message_role(request_type) == LLMMessageRole.DEVELOPER

    def test_returns_user_for_normal_chat_request(self, chat_service):
        assert (
            chat_service._get_message_role(ChatRequestType.CHAT) == LLMMessageRole.USER
        )


class TestCheckIfPreviousChatHistoriesExist:
    """check_if_previous_chat_histories_existのテスト。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("repo_result", [True, False])
    async def test_decrypts_position_id_and_returns_repository_result(
        self,
        repo_result,
        chat_service,
        mock_chat_repo,
    ):
        """position_idを復号化し、Repositoryの結果（True/False）をそのまま返すこと。"""
        mock_chat_repo.has_position_chat_histories.return_value = repo_result

        with patch("services.chat_service.decrypt") as mock_decrypt:
            mock_decrypt.return_value = "decrypted-position-123"

            result = await chat_service.check_if_previous_chat_histories_exist(
                "encrypted-pos"
            )

        mock_decrypt.assert_called_once()
        mock_chat_repo.has_position_chat_histories.assert_called_once_with(
            "decrypted-position-123"
        )
        assert result is repo_result


class TestLoadPreviousChatHistories:
    """load_previous_chat_historiesのテスト。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("encrypted_position_id", "before_id"),
        [
            (None, None),
            (None, "msg-123"),
            ("encrypted-pos", "msg-123"),
        ],
    )
    async def test_calls_correct_repository_and_returns_empty_when_no_histories(
        self,
        encrypted_position_id,
        before_id,
        chat_service,
        mock_chat_repo,
    ):
        """チャット種別に応じて正しいRepositoryを呼び、履歴なしの場合は([], True)を返すこと。"""
        if encrypted_position_id is None:
            mock_chat_repo.get_main_chat_histories.return_value = []

            result = await chat_service.load_previous_chat_histories(
                limit=5,
                encrypted_position_id=None,
                before_id=before_id,
            )

            mock_chat_repo.get_main_chat_histories.assert_called_once_with(before_id)
            assert result == ([], True)
            return

        mock_chat_repo.get_position_detail_chat_histories.return_value = []
        with patch(
            "services.chat_service.decrypt", return_value="decrypted-pos"
        ) as mock_decrypt:
            result = await chat_service.load_previous_chat_histories(
                limit=5,
                encrypted_position_id=encrypted_position_id,
                before_id=before_id,
            )

        mock_decrypt.assert_called_once()
        mock_chat_repo.get_position_detail_chat_histories.assert_called_once_with(
            "decrypted-pos",
            before_id,
        )
        assert result == ([], True)

    @pytest.mark.asyncio
    async def test_respects_limit_parameter(self, chat_service, mock_chat_repo):
        """limitで指定した件数分だけ会話（ユーザー単位）を返すこと。"""
        # user1 -> assistant1, user2 -> assistant2, user3 -> assistant3 の履歴を用意
        histories = [
            self._create_mock_history(1, LLMMessageRole.USER, "user1", "Hello 1"),
            self._create_mock_history(2, LLMMessageRole.ASSISTANT, "asst1", "Hi 1"),
            self._create_mock_history(3, LLMMessageRole.USER, "user2", "Hello 2"),
            self._create_mock_history(4, LLMMessageRole.ASSISTANT, "asst2", "Hi 2"),
            self._create_mock_history(5, LLMMessageRole.USER, "user3", "Hello 3"),
            self._create_mock_history(6, LLMMessageRole.ASSISTANT, "asst3", "Hi 3"),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        result, _ = await chat_service.load_previous_chat_histories(
            limit=2,
            encrypted_position_id=None,
            before_id=None,
        )

        # ユーザーメッセージ2件 + それに紐づくアシスタント応答2件の想定
        user_messages = self._find_messages_by_role(result, LLMMessageRole.USER)
        assert len(user_messages) == 2

    @pytest.mark.asyncio
    async def test_groups_user_message_with_assistant_response(
        self, chat_service, mock_chat_repo
    ):
        """ユーザーメッセージとアシスタント応答が同一会話として返ること。"""
        histories = [
            self._create_mock_history(1, LLMMessageRole.USER, "user1", "Hello"),
            self._create_mock_history(2, LLMMessageRole.ASSISTANT, "asst1", "Hi there"),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        result, _ = await chat_service.load_previous_chat_histories(
            limit=5,
            encrypted_position_id=None,
            before_id=None,
        )

        # 新->旧の順（アシスタント -> ユーザー）で返る
        assert len(result) == 2
        assert result[0]["Role"] == LLMMessageRole.ASSISTANT
        assert result[0]["Message"] == "Hi there"
        assert result[1]["Role"] == LLMMessageRole.USER
        assert result[1]["Message"] == "Hello"

    @pytest.mark.asyncio
    async def test_returns_only_first_assistant_message_after_user(
        self, chat_service, mock_chat_repo
    ):
        """ユーザーメッセージ後に複数のassistantが続く場合、最初のassistantのみ返すこと。"""
        histories = [
            self._create_mock_history(1, LLMMessageRole.USER, "user1", "Hello"),
            self._create_mock_history(
                2, LLMMessageRole.ASSISTANT, "asst1", "First reply"
            ),
            self._create_mock_history(
                3, LLMMessageRole.ASSISTANT, "asst2", "Second reply"
            ),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        result, _ = await chat_service.load_previous_chat_histories(
            limit=5,
            encrypted_position_id=None,
            before_id=None,
        )

        assistant_messages = self._find_messages_by_role(
            result, LLMMessageRole.ASSISTANT
        )
        assert len(assistant_messages) == 1
        assert assistant_messages[0]["MessageID"] == "asst1"
        assert assistant_messages[0]["Message"] == "First reply"

    @pytest.mark.asyncio
    async def test_returns_histories_in_id_desc_order(self, chat_service, mock_chat_repo):
        """返却結果がid降順（新→旧）になること。"""
        histories = [
            self._create_mock_history(1, LLMMessageRole.USER, "1", "Hello 1"),
            self._create_mock_history(2, LLMMessageRole.ASSISTANT, "2", "Hi 1"),
            self._create_mock_history(3, LLMMessageRole.USER, "3", "Hello 2"),
            self._create_mock_history(4, LLMMessageRole.ASSISTANT, "4", "Hi 2"),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        result, _ = await chat_service.load_previous_chat_histories(
            limit=5,
            encrypted_position_id=None,
            before_id=None,
        )

        message_ids = [r["MessageID"] for r in result]
        assert message_ids == ["4", "3", "2", "1"]

    @pytest.mark.asyncio
    async def test_excludes_session_start_message_from_user_messages(
        self, chat_service, mock_chat_repo
    ):
        """セッション開始メッセージ（developerロール）が結果に含まれないこと。"""
        histories = [
            self._create_mock_history(
                1, LLMMessageRole.DEVELOPER, "dev1", SESSION_START_MESSAGE
            ),
            self._create_mock_history(2, LLMMessageRole.ASSISTANT, "asst1", "Welcome!"),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        result, _ = await chat_service.load_previous_chat_histories(
            limit=5,
            encrypted_position_id=None,
            before_id=None,
        )

        # セッション開始developerメッセージは送信対象外（assistantのみが返る想定）
        user_messages = [
            r
            for r in result
            if r["Role"] == LLMMessageRole.USER or r["Role"] == LLMMessageRole.DEVELOPER
        ]
        assert len(user_messages) == 0

    @pytest.mark.asyncio
    async def test_sets_no_more_user_message_left_correctly_when_more_exist(
        self, chat_service, mock_chat_repo
    ):
        """未取得のユーザーメッセージが残っている場合、no_more=Falseとなること。"""
        histories = [
            self._create_mock_history(1, LLMMessageRole.USER, "user1", "First"),
            self._create_mock_history(
                2, LLMMessageRole.ASSISTANT, "asst1", "Response 1"
            ),
            self._create_mock_history(3, LLMMessageRole.USER, "user2", "Second"),
            self._create_mock_history(
                4, LLMMessageRole.ASSISTANT, "asst2", "Response 2"
            ),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        _, no_more = await chat_service.load_previous_chat_histories(
            limit=1,
            encrypted_position_id=None,
            before_id=None,
        )

        assert no_more is False

    @pytest.mark.asyncio
    async def test_sets_no_more_user_message_left_correctly_when_all_loaded(
        self, chat_service, mock_chat_repo
    ):
        """全てのユーザーメッセージを取得済みの場合、no_more=Trueとなること。"""
        histories = [
            self._create_mock_history(1, LLMMessageRole.USER, "user1", "Only message"),
            self._create_mock_history(2, LLMMessageRole.ASSISTANT, "asst1", "Response"),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        _, no_more = await chat_service.load_previous_chat_histories(
            limit=5,
            encrypted_position_id=None,
            before_id=None,
        )

        assert no_more is True

    @pytest.mark.asyncio
    async def test_includes_position_search_tool_results(self, chat_service, mock_chat_repo):
        """POSITION_SEARCHツール結果がレスポンスに含まれること。"""
        tool_history = self._create_mock_history(
            2,
            LLMMessageRole.TOOL,
            "tool1",
            '{"text": "{\\"positions\\": []}"}',
        )
        tool_history.tool_name = ToolName.GENERIC_POSITION_SEARCH
        tool_history.tool_call_id = "call-123"
        tool_history.tool_input = {
            "Salary": "500万円以上",
            "Locations": [
                {
                    "LocationType": LocationType.RESIDENCE,
                    "PrefectureName": "東京都",
                    "CityName": "渋谷区",
                }
            ],
        }

        histories = [
            self._create_mock_history(1, LLMMessageRole.USER, "user1", "Find jobs"),
            tool_history,
            self._create_mock_history(
                3, LLMMessageRole.ASSISTANT, "asst1", "Here are jobs"
            ),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        result, _ = await chat_service.load_previous_chat_histories(
            limit=5,
            encrypted_position_id=None,
            before_id=None,
        )

        tool_results = self._find_messages_by_role(result, LLMMessageRole.TOOL)
        assert len(tool_results) == 1
        assert tool_results[0]["Type"] == ChatResponseType.POSITION_SEARCH_LINK

    @pytest.mark.asyncio
    async def test_skips_tool_result_when_tool_output_is_error(
        self, chat_service, mock_chat_repo
    ):
        """ツール結果にMessage（エラー）が含まれる場合、ツール結果をスキップすること。"""
        tool_history = self._create_mock_history(
            2,
            LLMMessageRole.TOOL,
            "tool1",
            '{"text": "{\\"Message\\": \\"error\\"}"}',
        )
        tool_history.tool_name = ToolName.GENERIC_POSITION_SEARCH
        tool_history.tool_call_id = "call-123"
        tool_history.tool_input = {
            "Salary": "500万円以上",
            "Locations": [
                {
                    "LocationType": LocationType.RESIDENCE,
                    "PrefectureName": "東京都",
                    "CityName": "渋谷区",
                }
            ],
        }

        histories = [
            self._create_mock_history(1, LLMMessageRole.USER, "user1", "Find jobs"),
            tool_history,
            self._create_mock_history(
                3, LLMMessageRole.ASSISTANT, "asst1", "Here are jobs"
            ),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        result, _ = await chat_service.load_previous_chat_histories(
            limit=5,
            encrypted_position_id=None,
            before_id=None,
        )

        tool_results = self._find_messages_by_role(result, LLMMessageRole.TOOL)
        assert tool_results == []

    @pytest.mark.asyncio
    async def test_skips_tool_result_when_conditions_are_invalid(
        self, chat_service, mock_chat_repo
    ):
        """tool_inputの必須項目が欠けている場合、ツール結果をスキップすること。"""
        tool_history = self._create_mock_history(
            2,
            LLMMessageRole.TOOL,
            "tool1",
            '{"text": "{\\"positions\\": []}"}',
        )
        tool_history.tool_name = ToolName.GENERIC_POSITION_SEARCH
        tool_history.tool_call_id = None  # invalid
        tool_history.tool_input = {"Salary": "500万円以上", "Locations": []}

        histories = [
            self._create_mock_history(1, LLMMessageRole.USER, "user1", "Find jobs"),
            tool_history,
            self._create_mock_history(
                3, LLMMessageRole.ASSISTANT, "asst1", "Here are jobs"
            ),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        result, _ = await chat_service.load_previous_chat_histories(
            limit=5,
            encrypted_position_id=None,
            before_id=None,
        )

        tool_results = self._find_messages_by_role(result, LLMMessageRole.TOOL)
        assert tool_results == []

    @pytest.mark.asyncio
    async def test_includes_greeting_message_when_no_more_user_messages_left(
        self, chat_service, mock_chat_repo
    ):
        """全ユーザーメッセージ取得完了時、SESSION_START_MESSAGE後の挨拶メッセージが含まれること。"""
        histories = [
            self._create_mock_history(
                1, LLMMessageRole.DEVELOPER, "dev1", SESSION_START_MESSAGE
            ),
            self._create_mock_history(
                2,
                LLMMessageRole.ASSISTANT,
                "asst1",
                "初めまして!マイダス AI転職アドバイザーです。",
            ),
            self._create_mock_history(
                3, LLMMessageRole.USER, "user1", "求人を探して欲しい"
            ),
            self._create_mock_history(
                4, LLMMessageRole.ASSISTANT, "asst2", "承知しました"
            ),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        result, no_more = await chat_service.load_previous_chat_histories(
            limit=10,
            encrypted_position_id=None,
            before_id=None,
        )

        # 挨拶メッセージが含まれていることを確認
        greeting_messages = self._find_messages_by_role_and_id(
            result, LLMMessageRole.ASSISTANT, "asst1"
        )
        assert len(greeting_messages) == 1
        assert (
            greeting_messages[0]["Message"]
            == "初めまして!マイダス AI転職アドバイザーです。"
        )
        assert no_more is True

    @pytest.mark.asyncio
    async def test_does_not_include_greeting_when_more_user_messages_exist(
        self, chat_service, mock_chat_repo
    ):
        """未取得のユーザーメッセージが残っている場合、挨拶メッセージは含まれないこと。"""
        histories = [
            self._create_mock_history(
                1, LLMMessageRole.DEVELOPER, "dev1", SESSION_START_MESSAGE
            ),
            self._create_mock_history(
                2, LLMMessageRole.ASSISTANT, "asst1", "初めまして!"
            ),
            self._create_mock_history(3, LLMMessageRole.USER, "user1", "First message"),
            self._create_mock_history(
                4, LLMMessageRole.ASSISTANT, "asst2", "Response 1"
            ),
            self._create_mock_history(
                5, LLMMessageRole.USER, "user2", "Second message"
            ),
            self._create_mock_history(
                6, LLMMessageRole.ASSISTANT, "asst3", "Response 2"
            ),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        # limit=1なので1件のユーザーメッセージのみ取得、まだ残っている
        result, no_more = await chat_service.load_previous_chat_histories(
            limit=1,
            encrypted_position_id=None,
            before_id=None,
        )

        # 挨拶メッセージは含まれていないこと
        greeting_messages = self._find_messages_by_role_and_id(
            result, LLMMessageRole.ASSISTANT, "asst1"
        )
        assert len(greeting_messages) == 0
        assert no_more is False

    @pytest.mark.asyncio
    async def test_greeting_message_with_real_data_scenario(
        self, chat_service, mock_chat_repo
    ):
        """実際の会話データで挨拶メッセージが正しく含まれること。"""
        histories = [
            self._create_mock_history(
                9512,
                LLMMessageRole.DEVELOPER,
                "developer_20260126204622144890",
                "### ツール呼び出し時のパラメータについて\nSessionID: 8139badc-9269-4201-adee-4eb3a6b989fbを利用してください\nRequestID: Pythonの`uuid.uuid4()`を使って生成してください\n",
            ),
            self._create_mock_history(
                9513,
                LLMMessageRole.DEVELOPER,
                "developer_20260126204608217001",
                SESSION_START_MESSAGE,  # "会話開始"
            ),
            self._create_mock_history(
                9514,
                LLMMessageRole.ASSISTANT,
                "msg_0fb0371364a26d010069775406c1c081959b1e94fd20510c43",
                "初めまして!マイダス AI転職アドバイザーです。あなたにぴったりの求人探しから、初めての仕事の相談まで、理想のキャリア実現をサポートします。本日はどのようなご相談がお希望ですか?",
            ),
            self._create_mock_history(
                9515,
                LLMMessageRole.USER,
                "input_f05bee24-8eaf-4659-bb11-6271b4074c86",
                "求人を探して欲しい",
            ),
            self._create_mock_history(
                9516,
                LLMMessageRole.TOOL,
                "fc_0fb0371364a26d01006977540fe01081958a679d19c2d052ec",
                '{"assistant": "CareerAdvisor"}',
            ),
            self._create_mock_history(
                9517,
                LLMMessageRole.ASSISTANT,
                "msg_0fb0371364a26d01006977541303108195b43f5de597250979",
                "ありがとうございます!まずは求人をお探しするために、いくつか質問させてください。差し支えなければ、現在、お住まいの都道府県と市区町村(例:東京都新宿区、大阪府大阪市など)を教えていただけますか?(東京都の場合は、「区」まで、それ以外は、「市」までで大丈夫です)",
            ),
            self._create_mock_history(
                9518,
                LLMMessageRole.USER,
                "input_7198c1b0-cbcd-441a-ba5b-740f326721a0",
                "大阪市",
            ),
            self._create_mock_history(
                9519,
                LLMMessageRole.ASSISTANT,
                "msg_0c470f4e9e8627f8006977545888d4819792b50c90d0cea8bf",
                "ありがとうございます!大阪市ですね。もし差し支えなければ、住んでいる都道府県を教えていただけますか?(例:大阪府大阪市)  \n念のため正確な市区町村まで教えていただくと求人の「提案」がスムーズです",
            ),
            self._create_mock_history(
                9520,
                LLMMessageRole.USER,
                "input_eae22e36-0f13-4d6c-84e9-ee76d954d42f",
                "大阪市はいくつありますか?",
            ),
            self._create_mock_history(
                9521,
                LLMMessageRole.ASSISTANT,
                "msg_0c470f4e9e8627f8006977546dda548197b3a7016a9a0146d0",
                "ご質問ありがとうございます。「大阪市」は、「大阪府」に1つだけ存在しています。正式には「大阪府大阪市」となります。\n\nお手数ですが、もしよろしければ、「大阪府大阪市」で求人をお探しさせていただいてもよろしいでしょうか?",
            ),
            self._create_mock_history(
                9522,
                LLMMessageRole.USER,
                "input_5661f7ea-73e8-4800-b9c4-809b097063a1",
                "はい",
            ),
            self._create_mock_history(
                9523,
                LLMMessageRole.ASSISTANT,
                "msg_0c470f4e9e8627f800697754748e588197a84bb70b720b93d1",
                "ご回答ありがとうございます!次に、「ご希望の年収」を伺えますでしょうか?例えば、「最低◯◯万円以上」など、具体的な金額で教えていただけますと助かります",
            ),
            self._create_mock_history(
                9524,
                LLMMessageRole.USER,
                "input_8c00e13d-959e-41a7-9c82-db2d29b4b1e9",
                "400",
            ),
            self._create_mock_history(
                9525,
                LLMMessageRole.ASSISTANT,
                "msg_0c470f4e9e8627f800697754799ce48197a57ed597dfa22792",
                "ありがとうございます。ご希望年収は「400万円以上」で、お伺いしました。\n\n最後に、ご希望する「職種」ややってみたい「仕事」があれば教えていただけますか?(例:事務、営業、エンジニアなど、ざっくりとしたご希望で大丈夫です)",
            ),
            self._create_mock_history(
                9526,
                LLMMessageRole.ASSISTANT,
                "msg_0c470f4e9e8627f8006977547edb3481978548bda32249df4e",
                "ご希望の職種を伺えますでしょうか?どんなお仕事でも結構ですので、興味のある職種、やってみたい分野があれば教えてください",
            ),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        result, no_more = await chat_service.load_previous_chat_histories(
            limit=5,
            encrypted_position_id=None,
            before_id=None,
        )

        # 挨拶メッセージ(9514)が含まれることを確認
        greeting_msg = self._find_messages_by_message_id(
            result, "msg_0fb0371364a26d010069775406c1c081959b1e94fd20510c43"
        )
        assert len(greeting_msg) == 1
        assert (
            greeting_msg[0]["Message"]
            == "初めまして!マイダス AI転職アドバイザーです。あなたにぴったりの求人探しから、初めての仕事の相談まで、理想のキャリア実現をサポートします。本日はどのようなご相談がお希望ですか?"
        )
        assert greeting_msg[0]["Role"] == LLMMessageRole.ASSISTANT

        # SESSION_START_MESSAGEは含まれないこと（developerメッセージは送信対象外）
        session_start_msgs = self._find_messages_by_message_id(
            result, "developer_20260126204608217001"
        )
        assert len(session_start_msgs) == 0

        # 全てのユーザーメッセージとアシスタントメッセージが含まれることを確認
        user_messages = self._find_messages_by_role(result, LLMMessageRole.USER)
        assistant_messages = self._find_messages_by_role(
            result, LLMMessageRole.ASSISTANT
        )

        # ユーザーメッセージは5件（9515, 9518, 9520, 9522, 9524）
        assert len(user_messages) == 5
        # アシスタントメッセージは挨拶含め6件（9514の挨拶 + 9517, 9519, 9521, 9523, 9525/9526のいずれか1つ）
        # 9525と9526は連続したアシスタントメッセージなので1つだけ含まれる
        assert len(assistant_messages) == 6

        assert no_more is True

    @pytest.mark.asyncio
    async def test_greeting_message_order_in_result(self, chat_service, mock_chat_repo):
        """挨拶メッセージが結果の末尾（最古のメッセージ）に配置されること。"""
        histories = [
            self._create_mock_history(
                1, LLMMessageRole.DEVELOPER, "dev1", SESSION_START_MESSAGE
            ),
            self._create_mock_history(
                2, LLMMessageRole.ASSISTANT, "greeting", "Welcome!"
            ),
            self._create_mock_history(3, LLMMessageRole.USER, "user1", "Hello"),
            self._create_mock_history(4, LLMMessageRole.ASSISTANT, "asst1", "Hi there"),
        ]
        mock_chat_repo.get_main_chat_histories.return_value = histories

        result, _ = await chat_service.load_previous_chat_histories(
            limit=10,
            encrypted_position_id=None,
            before_id=None,
        )

        # 結果の順序: asst1, user1, greeting（新→旧）
        message_ids = [r["MessageID"] for r in result]
        assert message_ids == ["asst1", "user1", "greeting"]

    @staticmethod
    def _find_messages_by_message_id(result: list, message_id: str) -> list:
        """結果から特定のMessageIDを持つメッセージを抽出するヘルパー。"""
        return [r for r in result if r.get("MessageID") == message_id]

    @staticmethod
    def _find_messages_by_role_and_id(result: list, role: str, message_id: str) -> list:
        """結果から特定のRoleとMessageIDを持つメッセージを抽出するヘルパー。"""
        return [r for r in result if r["Role"] == role and r["MessageID"] == message_id]

    @staticmethod
    def _find_messages_by_role(result: list, role: str) -> list:
        """結果から特定のRoleを持つメッセージを抽出するヘルパー。"""
        return [r for r in result if r["Role"] == role]

    @staticmethod
    def _create_mock_history(
        id: int,
        role: str,
        message_id: str,
        content: str,
    ) -> Mock:
        """ChatHistoryのモックを生成するヘルパー。"""
        history = Mock(spec=ChatHistory)
        history.id = id
        history.role = role
        history.message_id = message_id
        history.content = content
        history.tool_name = None
        history.tool_call_id = None
        history.tool_input = None
        return history


class TestInitSession:
    """init_sessionメソッドのテスト"""

    @pytest.mark.asyncio
    async def test_calls_llm_service_clone_agents(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """llm_svc.clone_agents()が呼ばれること"""
        mock_agent1 = Mock(spec=Agent)
        mock_agent1.name = "CareerAdvisor"
        mock_agent2 = Mock(spec=Agent)
        mock_agent2.name = "PositionGuide"

        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent1, True),
            "PositionGuide": (mock_agent2, False),
        }

        mock_session = Mock()
        mock_session.histories = []
        mock_chat_repo.init_chat_session.return_value = (mock_session, False)

        await chat_service.init_session("gpt-4o")

        mock_llm_svc.clone_agents.assert_called_once_with("gpt-4o")

    @pytest.mark.asyncio
    async def test_stores_cloned_agents_in_service(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """クローンされたエージェントがサービスに保存されること"""
        mock_agent1 = Mock(spec=Agent)
        mock_agent1.name = "CareerAdvisor"
        mock_agent2 = Mock(spec=Agent)
        mock_agent2.name = "PositionGuide"

        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent1, True),
            "PositionGuide": (mock_agent2, False),
        }

        mock_session = Mock()
        mock_session.histories = []
        mock_chat_repo.init_chat_session.return_value = (mock_session, False)

        await chat_service.init_session("gpt-4o")

        assert "CareerAdvisor" in chat_service._agents
        assert "PositionGuide" in chat_service._agents
        assert chat_service._agents["CareerAdvisor"] == mock_agent1
        assert chat_service._agents["PositionGuide"] == mock_agent2

    @pytest.mark.asyncio
    async def test_sets_default_agent_as_active(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """default_agent=Trueのエージェントがアクティブになること"""
        mock_agent1 = Mock(spec=Agent)
        mock_agent1.name = "CareerAdvisor"
        mock_agent2 = Mock(spec=Agent)
        mock_agent2.name = "PositionGuide"

        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent1, True),  # default_agent=True
            "PositionGuide": (mock_agent2, False),
        }

        mock_session = Mock()
        mock_session.histories = []
        mock_chat_repo.init_chat_session.return_value = (mock_session, False)

        await chat_service.init_session("gpt-4o")

        assert chat_service._active_agent_name == "CareerAdvisor"

    @pytest.mark.asyncio
    async def test_initializes_new_session_when_no_existing_session(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """既存セッションがない場合に新規セッションを初期化すること"""
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (Mock(spec=Agent), True),
        }

        mock_chat_repo.init_chat_session.return_value = (None, False)

        with patch("services.chat_service.set_session_id") as mock_set_session_id:
            status, is_new = await chat_service.init_session("gpt-4o")

        assert status == ChatSessionStatus.CHATTING
        assert is_new is True
        mock_chat_repo.init_chat_session.assert_called_once()
        # 新規セッションの場合、session_idは変更されない
        mock_set_session_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_true_for_is_new_when_session_is_logically_deleted(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """セッションが論理削除されている場合、is_newがTrueを返すこと"""
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (Mock(spec=Agent), True),
        }

        # 論理削除されたセッション: existsはTrueだがsessionはNone
        # (deleted_atが設定されているセッションはリポジトリがNoneを返す想定)
        mock_chat_repo.init_chat_session.return_value = (None, True)

        mock_uuid = UUID("12345678-1234-5678-1234-567812345678")
        with patch("services.chat_service.uuid.uuid4", return_value=mock_uuid):
            with patch("services.chat_service.set_session_id") as mock_set_session_id:
                status, is_new = await chat_service.init_session("gpt-4o")

        assert status == ChatSessionStatus.CHATTING
        assert is_new is True  # 論理削除されたセッションは新規セッション扱い
        mock_set_session_id.assert_called_once_with(
            "12345678-1234-5678-1234-567812345678"
        )
        mock_chat_repo.init_chat_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_initializes_with_existing_session(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """既存セッションで初期化されることを確認"""
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (Mock(spec=Agent), True),
        }

        mock_session = Mock()
        mock_session.histories = []
        # existsがTrueの場合
        mock_chat_repo.init_chat_session.return_value = (mock_session, True)

        status, is_new = await chat_service.init_session("gpt-4o")

    @pytest.mark.asyncio
    async def test_loads_chat_histories_from_existing_session(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """既存セッションから会話履歴を読み込むこと"""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "CareerAdvisor"
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent, True),
        }

        # 会話履歴を作成
        history1 = Mock(spec=ChatHistory)
        history1.position_id = None
        history1.role = LLMMessageRole.USER
        history1.content = "Hello"
        history1.active_agent = "CareerAdvisor"

        history2 = Mock(spec=ChatHistory)
        history2.position_id = None
        history2.role = LLMMessageRole.ASSISTANT
        history2.content = "Hi there"
        history2.active_agent = "CareerAdvisor"

        mock_session = Mock()
        mock_session.status = ChatSessionStatus.CHATTING
        mock_session.histories = [history1, history2]
        mock_session.user_profile = None
        mock_chat_repo.init_chat_session.return_value = (mock_session, True)

        with patch.object(chat_service, "_convert_to_llm_messages") as mock_convert:
            mock_convert.return_value = ({"MAIN": [history1, history2]}, {"MAIN": []})
            status, is_new = await chat_service.init_session("gpt-4o")

        mock_convert.assert_called_once_with([history1, history2])
        assert status == ChatSessionStatus.CHATTING
        assert is_new is False

    @pytest.mark.asyncio
    async def test_finds_last_non_position_guide_agent(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """会話履歴から最後のPOSITION_GUIDE以外のエージェントを見つけること"""
        from services.llm_service import AgentName

        mock_agent1 = Mock(spec=Agent)
        mock_agent1.name = "CareerAdvisor"
        mock_agent2 = Mock(spec=Agent)
        mock_agent2.name = "PositionChangeAnalyze"
        mock_agent3 = Mock(spec=Agent)
        mock_agent3.name = AgentName.POSITION_GUIDE

        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent1, True),
            "PositionChangeAnalyze": (mock_agent2, False),
            AgentName.POSITION_GUIDE: (mock_agent3, False),
        }

        # 会話履歴を作成（最後のエージェントがPOSITION_GUIDEではない）
        history1 = Mock(spec=ChatHistory)
        history1.position_id = None
        history1.role = LLMMessageRole.USER
        history1.content = "Hello"
        history1.active_agent = "CareerAdvisor"

        history2 = Mock(spec=ChatHistory)
        history2.position_id = None
        history2.role = LLMMessageRole.ASSISTANT
        history2.content = "Hi"
        history2.active_agent = "CareerAdvisor"

        history3 = Mock(spec=ChatHistory)
        history3.position_id = "123"
        history3.role = LLMMessageRole.USER
        history3.content = "Tell me about this position"
        history3.active_agent = AgentName.POSITION_GUIDE

        mock_session = Mock()
        mock_session.status = ChatSessionStatus.CHATTING
        mock_session.histories = [history1, history2, history3]
        mock_session.user_profile = None
        mock_chat_repo.init_chat_session.return_value = (mock_session, True)

        with patch.object(chat_service, "_convert_to_llm_messages") as mock_convert:
            mock_convert.return_value = (
                {"MAIN": [history1, history2], "123": [history3]},
                {"MAIN": [], "123": []},
            )
            with patch.object(
                chat_service, "_find_last_non_position_guide_agent"
            ) as mock_find:
                mock_find.return_value = "CareerAdvisor"
                await chat_service.init_session("gpt-4o")

        mock_find.assert_called_once()
        assert chat_service._active_agent_name == "CareerAdvisor"

    @pytest.mark.asyncio
    async def test_does_not_load_user_profile_when_none(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """ユーザープロファイルがない場合は読み込まないこと"""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "CareerAdvisor"
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent, True),
        }

        mock_session = Mock()
        mock_session.status = ChatSessionStatus.CHATTING
        mock_session.histories = []
        mock_session.user_profile = None
        mock_chat_repo.init_chat_session.return_value = (mock_session, True)

        await chat_service.init_session("gpt-4o")

    @pytest.mark.asyncio
    async def test_sets_up_conversation_with_toolcall_trace_message(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """会話の初期設定にtoolcall_trace_messageが含まれること"""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "CareerAdvisor"
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent, True),
        }

        mock_chat_repo.init_chat_session.return_value = (None, False)

        await chat_service.init_session("gpt-4o")

        # MAIN会話にtoolcall_trace_messageが設定されていることを確認
        assert "MAIN" in chat_service._conversation
        assert len(chat_service._conversation["MAIN"]) == 1
        assert chat_service._conversation["MAIN"][0]["type"] == "message"
        assert chat_service._conversation["MAIN"][0]["role"] == LLMMessageRole.DEVELOPER
        assert "SessionID" in chat_service._conversation["MAIN"][0]["content"]

    @pytest.mark.asyncio
    async def test_returns_error_status_on_exception(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """例外が発生した場合にERRORステータスを返すこと"""
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (Mock(spec=Agent), True),
        }
        # init_chat_sessionで例外を発生させる
        mock_chat_repo.init_chat_session.side_effect = Exception("Test error")

        status, is_new = await chat_service.init_session("gpt-4o")

        assert status == ChatSessionStatus.ERROR
        assert is_new is False

    @pytest.mark.asyncio
    async def test_returns_session_status_when_session_exists(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """既存セッションが存在する場合、そのステータスを返すこと"""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "CareerAdvisor"
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent, True),
        }

        mock_history = Mock(spec=ChatHistory)
        mock_history.id = 1
        mock_history.session_id = "existing-session-id"
        mock_history.position_id = None
        mock_history.active_agent = "CareerAdvisor"
        mock_history.message_id = "msg-001"
        mock_history.role = LLMMessageRole.USER
        mock_history.content = "こんにちは"
        mock_history.tool_name = None
        mock_history.tool_call_id = None
        mock_history.tool_input = None
        mock_history.is_voice = None

        mock_session = Mock()
        mock_session.status = ChatSessionStatus.REGISTERING
        mock_session.histories = [mock_history]
        mock_session.user_profile = None
        mock_chat_repo.init_chat_session.return_value = (mock_session, True)

        status, is_new = await chat_service.init_session("gpt-4o")

        assert status == ChatSessionStatus.REGISTERING
        assert is_new is False

    @pytest.mark.asyncio
    async def test_stores_provider(self, chat_service, mock_llm_svc, mock_chat_repo):
        """providerが正しく保存されること"""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "CareerAdvisor"
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent, True),
        }

        mock_chat_repo.init_chat_session.return_value = (None, False)

        await chat_service.init_session("gpt-4o")

        assert chat_service._provider == "gpt-4o"

    @pytest.mark.asyncio
    async def test_creates_toolcall_trace_message_with_session_id(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """toolcall_trace_messageにSessionIDが含まれること"""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "CareerAdvisor"
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent, True),
        }

        mock_chat_repo.init_chat_session.return_value = (None, False)

        with patch(
            "services.chat_service.get_session_id", return_value="test-session-123"
        ):
            await chat_service.init_session("gpt-4o")

        assert chat_service._toolcall_trace_message is not None
        assert "test-session-123" in chat_service._toolcall_trace_message["content"]

    @pytest.mark.asyncio
    async def test_initializes_conversation_for_new_session(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """新規セッションの場合、会話を初期化すること"""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "CareerAdvisor"
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent, True),
        }

        mock_chat_repo.init_chat_session.return_value = (None, False)

        await chat_service.init_session("gpt-4o")

        assert "MAIN" in chat_service._conversation
        assert len(chat_service._conversation["MAIN"]) > 0

    @pytest.mark.asyncio
    async def test_treats_default_agent_only_session_as_new(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """DefaultAgentのみの会話履歴がある場合、新規セッションとして扱うこと"""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "CareerAdvisor"
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent, True),
        }

        history = Mock(spec=ChatHistory)
        history.position_id = None
        history.role = LLMMessageRole.ASSISTANT
        history.content = "こんにちは"
        history.active_agent = "DefaultAgent"

        mock_session = Mock()
        mock_session.status = ChatSessionStatus.CHATTING
        mock_session.histories = [history]
        mock_session.user_profile = None
        mock_chat_repo.init_chat_session.return_value = (mock_session, True)

        mock_uuid = "new-session-uuid"
        with patch.object(chat_service, "_convert_to_llm_messages") as mock_convert, \
             patch("services.chat_service.uuid.uuid4", return_value=mock_uuid), \
             patch("services.chat_service.set_session_id") as mock_set_session_id:
            mock_convert.return_value = ({"MAIN": [history]}, {"MAIN": []})
            status, is_new = await chat_service.init_session("gpt-4o")

        assert is_new is True
        assert chat_service._active_agent_name == ""
        # リセット後にtoolcall_trace_messageのみが設定されていること（旧履歴は消えている）
        assert list(chat_service._conversation.keys()) == ["MAIN"]
        assert len(chat_service._conversation["MAIN"]) == 1
        assert chat_service._chat_histories == {"MAIN": []}
        mock_set_session_id.assert_called_once_with(mock_uuid)

    @pytest.mark.asyncio
    async def test_keeps_existing_session_when_agent_is_known(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """既知エージェントの履歴がある場合、既存セッション再開として扱うこと"""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "CareerAdvisor"
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent, True),
        }

        history = Mock(spec=ChatHistory)
        history.position_id = None
        history.role = LLMMessageRole.ASSISTANT
        history.content = "求人を探しましょう"
        history.active_agent = "CareerAdvisor"

        mock_session = Mock()
        mock_session.status = ChatSessionStatus.CHATTING
        mock_session.histories = [history]
        mock_session.user_profile = None
        mock_chat_repo.init_chat_session.return_value = (mock_session, True)

        with patch.object(chat_service, "_convert_to_llm_messages") as mock_convert:
            mock_convert.return_value = ({"MAIN": [history]}, {"MAIN": []})
            status, is_new = await chat_service.init_session("gpt-4o")

        assert is_new is False
        assert chat_service._active_agent_name == "CareerAdvisor"

    @pytest.mark.asyncio
    async def test_treats_empty_history_session_as_new(
        self, chat_service, mock_llm_svc, mock_chat_repo
    ):
        """履歴のない既存セッション（孤立セッション）は新規セッションとして扱うこと"""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "CareerAdvisor"
        mock_llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (mock_agent, True),
        }

        mock_session = Mock()
        mock_session.status = ChatSessionStatus.CHATTING
        mock_session.histories = []
        mock_session.user_profile = None
        mock_chat_repo.init_chat_session.return_value = (mock_session, True)

        mock_uuid = "new-session-uuid"
        with patch("services.chat_service.uuid.uuid4", return_value=mock_uuid), \
             patch("services.chat_service.set_session_id") as mock_set_session_id:
            status, is_new = await chat_service.init_session("gpt-4o")

        assert is_new is True
        mock_set_session_id.assert_called_once_with(mock_uuid)


class TestGetInitialMenuResponse:
    """get_initial_menu_responseメソッドのテスト"""

    def test_returns_workflow_response_on_success(self, chat_service, mock_workflow_svc):
        """ワークフロー定義が取得できた場合、WORKFLOWレスポンスを返すこと"""
        from domain.entities.workflow_definition import WorkflowDefinition, DisplayType, SelectionType
        definition = WorkflowDefinition.model_validate({
            "id": "initial_menu",
            "name": "初期メニュー",
            "displayType": DisplayType.INLINE,
            "steps": [
                {
                    "id": 1,
                    "question": "Q",
                    "questionPrompt": "P",
                    "selectionType": SelectionType.SINGLE,
                    "options": [{"label": "Option1", "value": 1, "allowFreeText": False}],
                }
            ],
        })
        # get_definition は同期メソッドなので Mock（AsyncMock ではない）で上書き
        mock_workflow_svc.get_definition = Mock(return_value=definition)

        response = chat_service.get_initial_menu_response()

        assert response.response_type == ChatResponseType.WORKFLOW
        mock_workflow_svc.get_definition.assert_called_once_with("initial_menu")

    def test_returns_error_response_on_file_not_found(self, chat_service, mock_workflow_svc):
        """ワークフロー定義ファイルが存在しない場合、エラーレスポンスを返すこと"""
        mock_workflow_svc.get_definition = Mock(side_effect=FileNotFoundError("not found"))

        response = chat_service.get_initial_menu_response()

        assert response.response_type == ChatResponseType.ERROR

    def test_returns_error_response_on_value_error(self, chat_service, mock_workflow_svc):
        """ワークフロー定義が不正な場合、エラーレスポンスを返すこと"""
        mock_workflow_svc.get_definition = Mock(side_effect=ValueError("invalid"))

        response = chat_service.get_initial_menu_response()

        assert response.response_type == ChatResponseType.ERROR


class TestSummarizePositionDetailChat:
    """summarize_position_detail_chatメソッドのテスト"""

    @pytest.mark.asyncio
    async def test_calls_llm_service_summarize_method(
        self, chat_service, mock_conversation_summary_svc, mock_chat_repo
    ):
        """conversation_summary_svc.summarize_position_detail_chat()が呼ばれること"""
        # セットアップ
        encrypted_position_id = "encrypted-pos-123"
        decrypted_position_id = "decrypted-pos-123"

        chat_request = Mock()
        chat_request.position_id = encrypted_position_id

        # チャット履歴を設定
        history1 = Mock(spec=ChatHistory)
        history1.id = 1
        history1.role = LLMMessageRole.USER
        history1.content = "Tell me about this job"

        history2 = Mock(spec=ChatHistory)
        history2.id = 2
        history2.role = LLMMessageRole.ASSISTANT
        history2.content = "This is a great position"

        chat_service._chat_histories[decrypted_position_id] = [history1, history2]
        chat_service._conversation = {"MAIN": []}

        # モック設定
        mock_conversation_summary_svc.summarize_position_detail_chat.return_value = (
            "Summary text"
        )
        mock_session_status = Mock()
        mock_chat_repo.session_status.return_value = mock_session_status

        with patch("services.chat_service.decrypt", return_value=decrypted_position_id):
            with patch.object(chat_service, "_save_chat_histories"):
                result = await chat_service.summarize_position_detail_chat(chat_request)

        # 検証
        mock_conversation_summary_svc.summarize_position_detail_chat.assert_called_once_with(
            [history1, history2]
        )
        assert result == mock_session_status

    @pytest.mark.asyncio
    async def test_returns_session_status_when_no_position_id(
        self, chat_service, mock_conversation_summary_svc, mock_chat_repo
    ):
        """position_idがない場合にsession_statusを返すこと"""
        chat_request = Mock()
        chat_request.position_id = None

        mock_session_status = Mock()
        mock_chat_repo.session_status.return_value = mock_session_status

        result = await chat_service.summarize_position_detail_chat(chat_request)

        mock_conversation_summary_svc.summarize_position_detail_chat.assert_not_called()
        assert result == mock_session_status

    @pytest.mark.asyncio
    async def test_returns_session_status_when_decryption_fails(
        self, chat_service, mock_conversation_summary_svc, mock_chat_repo
    ):
        """position_idの復号化に失敗した場合にsession_statusを返すこと"""
        chat_request = Mock()
        chat_request.position_id = "encrypted-pos-123"

        mock_session_status = Mock()
        mock_chat_repo.session_status.return_value = mock_session_status

        with patch(
            "services.chat_service.decrypt", side_effect=Exception("Decryption error")
        ):
            result = await chat_service.summarize_position_detail_chat(chat_request)

        mock_conversation_summary_svc.summarize_position_detail_chat.assert_not_called()
        assert result == mock_session_status

    @pytest.mark.asyncio
    async def test_returns_session_status_when_no_chat_histories(
        self, chat_service, mock_conversation_summary_svc, mock_chat_repo
    ):
        """チャット履歴がない場合にsession_statusを返すこと"""
        chat_request = Mock()
        chat_request.position_id = "encrypted-pos-123"
        decrypted_position_id = "decrypted-pos-123"

        # 空の履歴を設定
        chat_service._chat_histories[decrypted_position_id] = []

        mock_session_status = Mock()
        mock_chat_repo.session_status.return_value = mock_session_status

        with patch("services.chat_service.decrypt", return_value=decrypted_position_id):
            result = await chat_service.summarize_position_detail_chat(chat_request)

        mock_conversation_summary_svc.summarize_position_detail_chat.assert_not_called()
        assert result == mock_session_status

    @pytest.mark.asyncio
    async def test_returns_session_status_when_summary_is_empty(
        self, chat_service, mock_conversation_summary_svc, mock_chat_repo
    ):
        """LLMサービスがNoneまたは空文字を返した場合にsession_statusを返すこと"""
        chat_request = Mock()
        chat_request.position_id = "encrypted-pos-123"
        decrypted_position_id = "decrypted-pos-123"

        history1 = Mock(spec=ChatHistory)
        history1.id = 1
        chat_service._chat_histories[decrypted_position_id] = [history1]

        mock_conversation_summary_svc.summarize_position_detail_chat.return_value = None
        mock_session_status = Mock()
        mock_chat_repo.session_status.return_value = mock_session_status

        with patch("services.chat_service.decrypt", return_value=decrypted_position_id):
            result = await chat_service.summarize_position_detail_chat(chat_request)

        assert result == mock_session_status

    @pytest.mark.asyncio
    async def test_saves_summary_to_database(
        self, chat_service, mock_conversation_summary_svc, mock_chat_repo
    ):
        """要約テキストがデータベースに保存されること"""
        chat_request = Mock()
        chat_request.position_id = "encrypted-pos-123"
        decrypted_position_id = "decrypted-pos-123"
        summary_text = "This is a summary of the chat"

        history1 = Mock(spec=ChatHistory)
        history1.id = 1
        chat_service._chat_histories[decrypted_position_id] = [history1]
        chat_service._conversation = {"MAIN": []}

        mock_conversation_summary_svc.summarize_position_detail_chat.return_value = (
            summary_text
        )
        mock_session_status = Mock()
        mock_chat_repo.session_status.return_value = mock_session_status

        with patch("services.chat_service.decrypt", return_value=decrypted_position_id):
            with patch.object(chat_service, "_save_chat_histories") as mock_save:
                await chat_service.summarize_position_detail_chat(chat_request)

                # _save_chat_historiesが呼ばれたことを確認
                mock_save.assert_called_once()
                saved_histories = mock_save.call_args[0][0]

                assert len(saved_histories) == 1
                assert saved_histories[0].role == LLMMessageRole.DEVELOPER
                assert saved_histories[0].content == summary_text
                assert saved_histories[0].position_id is None

    @pytest.mark.asyncio
    async def test_appends_summary_to_main_conversation(
        self, chat_service, mock_conversation_summary_svc, mock_chat_repo
    ):
        """要約がメイン会話履歴に追加されること"""
        chat_request = Mock()
        chat_request.position_id = "encrypted-pos-123"
        decrypted_position_id = "decrypted-pos-123"
        summary_text = "This is a summary of the chat"

        history1 = Mock(spec=ChatHistory)
        history1.id = 1
        chat_service._chat_histories[decrypted_position_id] = [history1]

        # _conversationを初期化
        chat_service._conversation = {"MAIN": []}

        mock_conversation_summary_svc.summarize_position_detail_chat.return_value = (
            summary_text
        )
        mock_session_status = Mock()
        mock_chat_repo.session_status.return_value = mock_session_status

        with patch("services.chat_service.decrypt", return_value=decrypted_position_id):
            with patch.object(chat_service, "_save_chat_histories"):
                await chat_service.summarize_position_detail_chat(chat_request)

        # メイン会話に追加されたことを確認
        assert len(chat_service._conversation["MAIN"]) == 1
        added_message = chat_service._conversation["MAIN"][0]
        assert added_message["type"] == "message"
        assert added_message["role"] == LLMMessageRole.DEVELOPER.value
        assert len(added_message["content"]) == 1
        assert added_message["content"][0]["text"] == summary_text

    @pytest.mark.asyncio
    async def test_generates_correct_message_id_format(
        self, chat_service, mock_conversation_summary_svc, mock_chat_repo
    ):
        """正しいフォーマットのmessage_idが生成されること"""
        chat_request = Mock()
        chat_request.position_id = "encrypted-pos-123"
        decrypted_position_id = "decrypted-pos-123"
        summary_text = "Summary"

        history1 = Mock(spec=ChatHistory)
        history1.id = 1
        chat_service._chat_histories[decrypted_position_id] = [history1]
        chat_service._conversation = {"MAIN": []}

        mock_conversation_summary_svc.summarize_position_detail_chat.return_value = (
            summary_text
        )
        mock_session_status = Mock()
        mock_chat_repo.session_status.return_value = mock_session_status

        with patch("services.chat_service.decrypt", return_value=decrypted_position_id):
            with patch.object(chat_service, "_save_chat_histories") as mock_save:
                await chat_service.summarize_position_detail_chat(chat_request)

                saved_histories = mock_save.call_args[0][0]
                message_id = saved_histories[0].message_id

                # message_idが正しいプレフィックスで始まることを確認
                assert message_id.startswith(
                    f"position_detail_chat_summary_{decrypted_position_id}_"
                )
                # タイムスタンプ部分が数字であることを確認
                timestamp_part = message_id.split("_")[-1]
                assert timestamp_part.isdigit()


class FakeRunResult:
    def __init__(
        self,
        events: list,
        input_list: list | None = None,
        *,
        last_agent_name: str | None = None,
        last_response_id: str = "resp-1",
    ):
        self._events = events
        self._input_list = input_list or []
        self.last_response_id = last_response_id
        self.last_agent = None
        if last_agent_name is not None:
            self.last_agent = Mock(spec=Agent)
            self.last_agent.name = last_agent_name
        self.context_wrapper = Mock()
        self.context_wrapper.usage = {"input_tokens": 1, "output_tokens": 1}

    async def stream_events(self):
        for event in self._events:
            yield event

    def to_input_list(self) -> list:
        return self._input_list


class FakeStreamEvent:
    def __init__(self, event_type: str, *, data=None, item=None):
        self.type = event_type
        self.data = data
        self.item = item


class FakeToolCallItem:
    def __init__(self, raw_item):
        self.raw_item = raw_item
        self.agent = Mock()
        self.agent.tool_use_behavior = {}


class FakeToolCallOutputItem:
    def __init__(self, raw_item: dict):
        self.raw_item = raw_item


class FakeHandoffOutputItem:
    def __init__(self, target_agent_name: str):
        self.target_agent = Mock(spec=Agent)
        self.target_agent.name = target_agent_name


class TestToolOutputNormalization:
    def test_parse_tool_output_accepts_structured_output_list(self, chat_service):
        parsed = chat_service._parse_tool_output(
            [
                {
                    "type": "input_text",
                    "text": '{"Message": "error"}',
                }
            ]
        )

        assert parsed == {"Message": "error"}

    def test_parse_tool_output_accepts_structured_payload(self, chat_service):
        parsed = chat_service._parse_tool_output({"text": '{"Message": "error"}'})

        assert parsed == {"Message": "error"}

    def test_parse_tool_output_accepts_already_parsed_inner_payload(self, chat_service):
        parsed = chat_service._parse_tool_output({"Message": "error"})

        assert parsed == {"Message": "error"}

    @pytest.mark.asyncio
    async def test_save_chat_history_serializes_structured_tool_output(
        self, chat_service, mock_chat_repo
    ):
        with patch("services.chat_service.ToolCallOutputItem", FakeToolCallOutputItem):
            await chat_service._save_chat_history(
                FakeToolCallOutputItem(
                    {
                        "call_id": "tool-call-1",
                        "output": {"text": "{}"},
                    }
                )
            )

        mock_chat_repo.update_tool_output.assert_called_once_with(
            tool_call_id="tool-call-1",
            tool_call_output='{"text": "{}"}',
        )


class TestChatStreamingCompatibility:
    @staticmethod
    def _build_chat_request() -> ChatRequestModel:
        return ChatRequestModel(
            request_type=ChatRequestType.CHAT,
            current_page=PageName.CHAT,
            message="こんにちは",
            current_message_id="msg-stream-1",
        )

    @staticmethod
    def _prepare_chat_service_for_chat(chat_service, mock_chat_repo):
        default_agent = Mock(spec=Agent)
        default_agent.name = "CareerAdvisor"
        final_agent = Mock(spec=Agent)
        final_agent.name = "FinalAgent"
        chat_service._agents = {
            "CareerAdvisor": default_agent,
            "FinalAgent": final_agent,
        }
        chat_service._active_agent_name = "CareerAdvisor"
        chat_service._conversation = {"MAIN": []}
        chat_service._chat_key = "MAIN"

        mock_chat_repo.session_status.return_value = ChatSessionStatus.CHATTING
        mock_chat_repo.is_session_blocked.return_value = False
        chat_service.llm_output_guard.reset_session_for_new_response = Mock()
        chat_service.llm_output_guard.process_stream_chunk = Mock(return_value=[])
        chat_service.llm_output_guard.finalize_stream = Mock(return_value=[])
        chat_service.llm_output_guard.remove_session = Mock()

    @pytest.mark.asyncio
    async def test_run_streamed_receives_previous_response_id(
        self, chat_service, mock_chat_repo
    ):
        self._prepare_chat_service_for_chat(chat_service, mock_chat_repo)
        chat_service._previous_response_ids["MAIN"] = "resp-prev"
        run_result = FakeRunResult(
            [],
            last_agent_name="CareerAdvisor",
            last_response_id="resp-next",
        )

        with (
            patch(
                "services.chat_service.Runner.run_streamed",
                return_value=run_result,
            ) as mock_run_streamed,
            patch.object(chat_service, "_save_chat_history"),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            _ = [
                chunk
                async for chunk in chat_service.chat(
                    self._build_chat_request(),
                    client_ip="127.0.0.1",
                )
            ]

        kwargs = mock_run_streamed.call_args.kwargs
        assert kwargs["previous_response_id"] == "resp-prev"
        assert "run_config" not in kwargs
        assert chat_service._previous_response_ids["MAIN"] == "resp-next"

    @pytest.mark.asyncio
    async def test_skip_build_summary_context_when_previous_response_id_exists(
        self, chat_service, mock_chat_repo
    ):
        self._prepare_chat_service_for_chat(chat_service, mock_chat_repo)
        chat_service._previous_response_ids["MAIN"] = "resp-prev"
        run_result = FakeRunResult([])

        with (
            patch.object(
                chat_service, "build_summary_context"
            ) as mock_build_summary_context,
            patch("services.chat_service.Runner.run_streamed", return_value=run_result),
            patch.object(chat_service, "_save_chat_history"),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            _ = [
                chunk
                async for chunk in chat_service.chat(
                    self._build_chat_request(),
                    client_ip="127.0.0.1",
                )
            ]

        mock_build_summary_context.assert_not_called()

    @pytest.mark.asyncio
    async def test_build_summary_context_when_previous_response_id_missing(
        self, chat_service, mock_chat_repo
    ):
        self._prepare_chat_service_for_chat(chat_service, mock_chat_repo)
        run_result = FakeRunResult([])

        with (
            patch.object(
                chat_service, "build_summary_context"
            ) as mock_build_summary_context,
            patch("services.chat_service.Runner.run_streamed", return_value=run_result),
            patch.object(chat_service, "_save_chat_history"),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            _ = [
                chunk
                async for chunk in chat_service.chat(
                    self._build_chat_request(),
                    client_ip="127.0.0.1",
                )
            ]

        mock_build_summary_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_last_agent_wins_over_streaming_handoff_updates(
        self, chat_service, mock_chat_repo
    ):
        self._prepare_chat_service_for_chat(chat_service, mock_chat_repo)
        run_result = FakeRunResult(
            [
                FakeStreamEvent(
                    "run_item_stream_event",
                    item=FakeHandoffOutputItem("IntermediateAgent"),
                )
            ],
            last_agent_name="FinalAgent",
        )

        with (
            patch("services.chat_service.HandoffOutputItem", FakeHandoffOutputItem),
            patch("services.chat_service.Runner.run_streamed", return_value=run_result),
            patch.object(chat_service, "_save_chat_history"),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            _ = [
                chunk
                async for chunk in chat_service.chat(
                    self._build_chat_request(),
                    client_ip="127.0.0.1",
                )
            ]

        assert chat_service._active_agent_name == "FinalAgent"


class TestChatJobtypeSearchFlow:
    @staticmethod
    def _build_chat_request() -> ChatRequestModel:
        return ChatRequestModel(
            request_type=ChatRequestType.CHAT,
            current_page=PageName.CHAT,
            message="職種を探したい",
            current_message_id="msg-1",
        )

    @staticmethod
    def _prepare_chat_service_for_chat(chat_service, mock_chat_repo):
        chat_service._agents = {"CareerAdvisor": Mock(spec=Agent)}
        chat_service._active_agent_name = "CareerAdvisor"
        chat_service._conversation = {"MAIN": []}
        chat_service._chat_key = "MAIN"

        mock_chat_repo.session_status.return_value = ChatSessionStatus.CHATTING
        mock_chat_repo.is_session_blocked.return_value = False
        chat_service.llm_output_guard.reset_session_for_new_response = Mock()
        chat_service.llm_output_guard.process_stream_chunk = Mock(return_value=[])
        chat_service.llm_output_guard.finalize_stream = Mock(return_value=[])
        chat_service.llm_output_guard.remove_session = Mock()

    @pytest.mark.asyncio
    async def test_returns_jobtype_search_result_on_tool_success(
        self,
        chat_service,
        mock_chat_repo,
    ):
        self._prepare_chat_service_for_chat(chat_service, mock_chat_repo)

        raw_tool_call = SimpleNamespace(
            call_id="tool-call-1",
            name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS.value,
            arguments='{"SessionID":"s","RequestID":"r"}',
        )

        events = [
            FakeStreamEvent(
                "run_item_stream_event", item=FakeToolCallItem(raw_tool_call)
            ),
            FakeStreamEvent(
                "run_item_stream_event",
                item=FakeToolCallOutputItem(
                    {
                        "call_id": "tool-call-1",
                        "output": '{"text":"{}"}',
                    }
                ),
            ),
        ]
        run_result = FakeRunResult(events)

        with (
            patch("services.chat_service.ToolCallItem", FakeToolCallItem),
            patch("services.chat_service.ToolCallOutputItem", FakeToolCallOutputItem),
            patch("services.chat_service.Runner.run_streamed", return_value=run_result),
            patch.object(chat_service, "_save_chat_history"),
            patch.object(
                chat_service,
                "_parse_tool_output",
                return_value={"職種": [{"職種名": "営業", "職種説明": "法人営業"}]},
            ),
            patch.object(
                chat_service,
                "_process_jobtype_search_result",
                return_value={
                    "ToolCall": {
                        "ID": "tool-call-1",
                        "Name": ToolName.JOBTYPE_SEARCH_BY_KEYWORDS.value,
                        "Arguments": "{}",
                    },
                    "Jobtypes": [{"ID": "営業", "Name": "法人営業"}],
                },
            ),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            responses = [
                chunk.model_copy(deep=True)
                async for chunk in chat_service.chat(
                    self._build_chat_request(),
                    client_ip="127.0.0.1",
                )
            ]

        response_types = [chunk.response_type for chunk in responses]
        assert ChatResponseType.JOBTYPE_SEARCH_RESULT in response_types

    @pytest.mark.asyncio
    async def test_saves_extra_history_after_jobtype_result(
        self,
        chat_service,
        mock_chat_repo,
    ):
        self._prepare_chat_service_for_chat(chat_service, mock_chat_repo)

        raw_tool_call = SimpleNamespace(
            call_id="tool-call-1",
            name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS.value,
            arguments='{"SessionID":"s","RequestID":"r"}',
        )

        extra_item_after_break = Mock(name="extra_item_after_break")
        events = [
            FakeStreamEvent(
                "run_item_stream_event", item=FakeToolCallItem(raw_tool_call)
            ),
            FakeStreamEvent(
                "run_item_stream_event",
                item=FakeToolCallOutputItem(
                    {
                        "call_id": "tool-call-1",
                        "output": '{"text":"{}"}',
                    }
                ),
            ),
            FakeStreamEvent("run_item_stream_event", item=extra_item_after_break),
        ]
        run_result = FakeRunResult(events)

        with (
            patch("services.chat_service.ToolCallItem", FakeToolCallItem),
            patch("services.chat_service.ToolCallOutputItem", FakeToolCallOutputItem),
            patch("services.chat_service.Runner.run_streamed", return_value=run_result),
            patch.object(chat_service, "_save_chat_history") as mock_save_chat_history,
            patch.object(
                chat_service,
                "_parse_tool_output",
                return_value={"職種": [{"職種名": "営業", "職種説明": "法人営業"}]},
            ),
            patch.object(
                chat_service,
                "_process_jobtype_search_result",
                return_value={
                    "ToolCall": {
                        "ID": "tool-call-1",
                        "Name": ToolName.JOBTYPE_SEARCH_BY_KEYWORDS.value,
                        "Arguments": "{}",
                    },
                    "Jobtypes": [{"ID": "営業", "Name": "法人営業"}],
                },
            ),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            _ = [
                chunk
                async for chunk in chat_service.chat(
                    self._build_chat_request(),
                    client_ip="127.0.0.1",
                )
            ]

        # 職種検索結果を返した後も stream は最後まで読み切るため、後続イベントも保存されること
        assert mock_save_chat_history.call_count == 3
        mock_save_chat_history.assert_any_call(events[0].item)
        mock_save_chat_history.assert_any_call(events[1].item)
        mock_save_chat_history.assert_any_call(extra_item_after_break)


class TestChatStopAtToolFlow:
    @staticmethod
    def _build_chat_request() -> ChatRequestModel:
        return ChatRequestModel(
            request_type=ChatRequestType.CHAT,
            current_page=PageName.CHAT,
            message="求人を探したい",
            current_message_id="msg-stop-at-1",
        )

    @staticmethod
    def _prepare_chat_service_for_chat(chat_service, mock_chat_repo):
        chat_service._agents = {"CareerAdvisor": Mock(spec=Agent)}
        chat_service._active_agent_name = "CareerAdvisor"
        chat_service._conversation = {"MAIN": []}
        chat_service._chat_key = "MAIN"

        mock_chat_repo.session_status.return_value = ChatSessionStatus.CHATTING
        mock_chat_repo.is_session_blocked.return_value = False
        chat_service.llm_output_guard.reset_session_for_new_response = Mock()
        chat_service.llm_output_guard.process_stream_chunk = Mock(return_value=[])
        chat_service.llm_output_guard.finalize_stream = Mock(return_value=[])
        chat_service.llm_output_guard.remove_session = Mock()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "position_tool_name",
        [
            ToolName.IT_POSITION_SEARCH.value,
            ToolName.FINANCIAL_SALES_POSITION_SEARCH.value,
        ],
    )
    async def test_stop_at_tool_adds_fake_position_search_result_to_conversation(
        self,
        position_tool_name,
        chat_service,
        mock_chat_repo,
    ):
        self._prepare_chat_service_for_chat(chat_service, mock_chat_repo)

        raw_tool_call = SimpleNamespace(
            call_id="position-call-1",
            name=position_tool_name,
            arguments='{"SessionID":"s","RequestID":"r"}',
        )
        tool_call_item = FakeToolCallItem(raw_tool_call)
        tool_call_item.agent.tool_use_behavior = {
            "stop_at_tool_names": [position_tool_name]
        }

        run_result = FakeRunResult(
            events=[
                FakeStreamEvent("run_item_stream_event", item=tool_call_item),
            ],
            input_list=[
                {
                    "type": "function_call_output",
                    "call_id": "position-call-1",
                    "output": "dummy output",
                }
            ],
        )

        with (
            patch("services.chat_service.ToolCallItem", FakeToolCallItem),
            patch("services.chat_service.ToolCallOutputItem", FakeToolCallOutputItem),
            patch("services.chat_service.Runner.run_streamed", return_value=run_result),
            patch.object(chat_service, "_save_chat_history"),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            _ = [
                chunk.model_copy(deep=True)
                async for chunk in chat_service.chat(
                    self._build_chat_request(),
                    client_ip="127.0.0.1",
                )
            ]

        function_call_outputs = [
            item
            for item in chat_service._conversation["MAIN"]
            if item.get("type") == "function_call_output"
            and item.get("call_id") == "position-call-1"
        ]
        assert len(function_call_outputs) == 1
        assert function_call_outputs[0][
            "output"
        ] == chat_service._generate_position_search_fake_result(0)


class TestHandleToolCallItem:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "tool_name",
        [
            ToolName.GENERIC_POSITION_SEARCH.value,
            ToolName.IT_POSITION_SEARCH.value,
            ToolName.FINANCIAL_SALES_POSITION_SEARCH.value,
        ],
    )
    async def test_position_search_tools_apply_rate_limit_and_input_parsing(
        self,
        tool_name,
        chat_service,
    ):
        tool_calls = {}
        item = SimpleNamespace(
            raw_item=SimpleNamespace(
                name=tool_name,
                arguments='{"SessionID":"s","RequestID":"r","Salary":500}',
            )
        )
        ensure_available = AsyncMock()

        with patch.object(
            chat_service,
            "_ensure_tool_execution_available",
            ensure_available,
        ):
            await chat_service._handle_tool_call_item(
                item=item,
                tool_calls=tool_calls,
                client_ip="127.0.0.1",
            )

        ensure_available.assert_awaited_once_with("127.0.0.1")
        assert ToolName(tool_name) in tool_calls


class TestExtractSelectedJobtypes:
    def test_returns_selected_jobtypes_from_expected_shape(self, chat_service):
        current_search_filter = {
            "SearchFilters": {
                "Jobtypes": {
                    "CategoryA": [
                        {"Value": "IT", "Selected": True},
                        {"Value": "Sales", "Selected": False},
                    ],
                    "CategoryB": [
                        {"Value": "Finance", "Selected": True},
                        {"Value": "IT", "Selected": True},
                    ],
                }
            }
        }

        result = chat_service._extract_selected_jobtypes(current_search_filter)

        assert result == ["IT", "Finance"]

    def test_warns_and_returns_empty_when_jobtypes_is_not_dict(self, chat_service):
        current_search_filter = {
            "SearchFilters": {
                "Jobtypes": [
                    {"Value": "IT", "Selected": True},
                    {"Value": "Finance", "Selected": True},
                ]
            }
        }

        with patch.object(chat_service.logger, "warning") as mock_warning:
            result = chat_service._extract_selected_jobtypes(current_search_filter)

        assert result == []
        mock_warning.assert_called_once_with(
            "Unexpected SearchFilters.Jobtypes shape: expected dict, got %s",
            "list",
        )

    def test_warns_and_skips_group_when_group_items_is_not_list(self, chat_service):
        current_search_filter = {
            "SearchFilters": {
                "Jobtypes": {
                    "CategoryA": {"Value": "IT", "Selected": True},
                    "CategoryB": [{"Value": "Finance", "Selected": True}],
                }
            }
        }

        with patch.object(chat_service.logger, "warning") as mock_warning:
            result = chat_service._extract_selected_jobtypes(current_search_filter)

        assert result == ["Finance"]
        mock_warning.assert_called_once_with(
            "Unexpected SearchFilters.Jobtypes[%s] shape: expected list, got %s",
            "CategoryA",
            "dict",
        )


class TestWorkflowSubmitted:
    """workflow_submittedのテスト"""

    @pytest.mark.asyncio
    async def test_workflow_submitted_success(self, chat_service, mock_workflow_svc):
        """ワークフロー回答時の正常系テスト"""
        mock_workflow_svc.process_workflow_submission.return_value = (
            WorkflowPostProcessingResult(message="LLMへの指示メッセージ"),
            [{"role": "assistant", "content": "Q1"}, {"role": "user", "content": "A1"}],
        )

        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps({"workflow_id": "test_wf", "answers": {"1": []}}),
            current_page=PageName.CHAT,
        )

        with patch.object(chat_service, "chat", return_value=AsyncMock()) as mock_chat:
            mock_chat.return_value.__aiter__.return_value = []

            async for _ in chat_service.workflow_submitted(input_data, "127.0.0.1"):
                pass

            mock_workflow_svc.process_workflow_submission.assert_called_once()
            assert chat_service._chat_repository.add_chat_histories.called
            histories = chat_service._chat_repository.add_chat_histories.call_args[0][0]
            assert len(histories) == 2
            assert histories[0].message_id.startswith("wf_test_wf_")

    @pytest.mark.asyncio
    async def test_workflow_submitted_validation_error(
        self, chat_service, mock_workflow_svc
    ):
        """ワークフローバリデーションエラー時のテスト"""
        mock_workflow_svc.process_workflow_submission.side_effect = ValueError(
            "バリデーション失敗"
        )

        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps({"workflow_id": "test_wf", "answers": {"1": []}}),
            current_page=PageName.CHAT,
        )

        responses = []
        async for resp in chat_service.workflow_submitted(input_data, "127.0.0.1"):
            responses.append(resp)

        assert len(responses) == 1
        assert responses[0].response_type == ChatResponseType.ERROR
        assert "バリデーション失敗" in responses[0].message
        assert not chat_service._chat_repository.add_chat_histories.called

    @pytest.mark.asyncio
    async def test_workflow_submitted_job_match_diagnosis_calls_apply_jobtypes(
        self, chat_service, mock_workflow_svc
    ):
        """selected_jobtypes がある場合、_apply_jobtypes_and_update_agents が呼ばれるテスト"""
        mock_workflow_svc.process_workflow_submission.return_value = (
            WorkflowPostProcessingResult(
                message="LLMへの指示メッセージ",
                selected_jobtypes=["システムエンジニア", "Webエンジニア"],
            ),
            [],
        )

        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "job_match_diagnosis", "answers": {"1": [], "3": []}}
            ),
            current_page=PageName.CHAT,
        )

        with (
            patch.object(
                chat_service,
                "_apply_jobtypes_and_update_agents",
                new_callable=AsyncMock,
                return_value=None,
            ) as mock_apply,
            patch.object(chat_service, "chat", return_value=AsyncMock()) as mock_chat,
        ):
            mock_chat.return_value.__aiter__.return_value = []

            async for _ in chat_service.workflow_submitted(input_data, "127.0.0.1"):
                pass

            mock_apply.assert_called_once_with(
                ["システムエンジニア", "Webエンジニア"],
                ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            )
            mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_submitted_job_match_diagnosis_apply_fails(
        self, chat_service, mock_workflow_svc
    ):
        """_apply_jobtypes_and_update_agents がエラーを返した場合、早期リターンするテスト"""
        mock_workflow_svc.process_workflow_submission.return_value = (
            WorkflowPostProcessingResult(
                message="LLMへの指示メッセージ",
                selected_jobtypes=["未サポート職種"],
            ),
            [],
        )
        error_resp = ChatStreamResponse(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED
        ).create_error_response("該当職種がまだサポートされていません。")

        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "job_match_diagnosis", "answers": {"1": [], "3": []}}
            ),
            current_page=PageName.CHAT,
        )

        with (
            patch.object(
                chat_service,
                "_apply_jobtypes_and_update_agents",
                new_callable=AsyncMock,
                return_value=error_resp,
            ),
            patch.object(chat_service, "chat", return_value=AsyncMock()) as mock_chat,
        ):
            mock_chat.return_value.__aiter__.return_value = []

            responses = []
            async for resp in chat_service.workflow_submitted(input_data, "127.0.0.1"):
                responses.append(resp)

            mock_chat.assert_not_called()
            assert len(responses) == 1
            assert responses[0].response_type == ChatResponseType.ERROR

    @pytest.mark.asyncio
    async def test_workflow_submitted_no_selected_jobtypes_skips_tool_update(
        self, chat_service, mock_workflow_svc
    ):
        """selected_jobtypes が None の場合、_apply_jobtypes_and_update_agents が呼ばれないテスト"""
        mock_workflow_svc.process_workflow_submission.return_value = (
            WorkflowPostProcessingResult(message="LLMへの指示メッセージ"),
            [],
        )

        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps({"workflow_id": "generic_wf", "answers": {"1": []}}),
            current_page=PageName.CHAT,
        )

        with (
            patch.object(
                chat_service,
                "_apply_jobtypes_and_update_agents",
                new_callable=AsyncMock,
            ) as mock_apply,
            patch.object(chat_service, "chat", return_value=AsyncMock()) as mock_chat,
        ):
            mock_chat.return_value.__aiter__.return_value = []

            async for _ in chat_service.workflow_submitted(input_data, "127.0.0.1"):
                pass

            mock_apply.assert_not_called()
            mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_submitted_initial_menu_sets_agent_and_creates_session(
        self, chat_service, mock_workflow_svc, mock_chat_repo
    ):
        """initial_menu: next_agent_name でエージェントを設定し、セッションを作成すること"""
        chat_service._toolcall_trace_message = {"type": "message", "role": "developer", "content": "trace"}
        mock_workflow_svc.process_workflow_submission.return_value = (
            WorkflowPostProcessingResult(
                message="求人検索を開始してください",
                next_agent_name="CareerAdvisor",
            ),
            [{"role": "assistant", "content": "選択肢"}, {"role": "user", "content": "求人検索"}],
        )

        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps({"workflow_id": "initial_menu", "answers": {"1": [{"value": 1}]}}),
            current_page=PageName.CHAT,
        )

        with patch.object(chat_service, "chat", return_value=AsyncMock()) as mock_chat:
            mock_chat.return_value.__aiter__.return_value = []

            async for _ in chat_service.workflow_submitted(input_data, "127.0.0.1"):
                pass

        assert chat_service._active_agent_name == "CareerAdvisor"
        mock_chat_repo.create_chat_session.assert_called_once()
        mock_chat.assert_called_once()
        chat_input = mock_chat.call_args[0][0]
        assert chat_input.message == "求人検索を開始してください"

    @pytest.mark.asyncio
    async def test_workflow_submitted_initial_menu_saves_toolcall_trace(
        self, chat_service, mock_workflow_svc, mock_chat_repo
    ):
        """initial_menu: toolcall_trace が DEVELOPER role で最初に add_chat_histories へ保存されること"""
        chat_service._toolcall_trace_message = {
            "type": "message",
            "role": "developer",
            "content": "trace-content",
        }
        mock_workflow_svc.process_workflow_submission.return_value = (
            WorkflowPostProcessingResult(
                message="開始します",
                next_agent_name="CareerAdvisor",
            ),
            [{"role": "assistant", "content": "選択肢"}],
        )

        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps({"workflow_id": "initial_menu", "answers": {"1": [{"value": 1}]}}),
            current_page=PageName.CHAT,
        )

        with patch.object(chat_service, "chat", return_value=AsyncMock()) as mock_chat:
            mock_chat.return_value.__aiter__.return_value = []
            async for _ in chat_service.workflow_submitted(input_data, "127.0.0.1"):
                pass

        first_call_histories = mock_chat_repo.add_chat_histories.call_args_list[0].args[0]
        assert len(first_call_histories) == 1
        assert first_call_histories[0].role == LLMMessageRole.DEVELOPER
        assert first_call_histories[0].content == "trace-content"

    @pytest.mark.asyncio
    async def test_workflow_submitted_initial_menu_history_saved_with_correct_agent(
        self, chat_service, mock_workflow_svc
    ):
        """initial_menu: 会話履歴が next_agent_name で保存されること"""
        chat_service._toolcall_trace_message = {"type": "message", "role": "developer", "content": "trace"}
        mock_workflow_svc.process_workflow_submission.return_value = (
            WorkflowPostProcessingResult(
                message="転職理由診断を開始してください",
                next_agent_name="PositionChangeAnalyze",
            ),
            [{"role": "assistant", "content": "Q"}, {"role": "user", "content": "転職理由診断"}],
        )

        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps({"workflow_id": "initial_menu", "answers": {"1": [{"value": 3}]}}),
            current_page=PageName.CHAT,
        )

        with patch.object(chat_service, "chat", return_value=AsyncMock()) as mock_chat:
            mock_chat.return_value.__aiter__.return_value = []

            async for _ in chat_service.workflow_submitted(input_data, "127.0.0.1"):
                pass

        saved = chat_service._chat_repository.add_chat_histories.call_args[0][0]
        assert all(h.active_agent == "PositionChangeAnalyze" for h in saved)

    @pytest.mark.asyncio
    async def test_workflow_submitted_initial_menu_next_workflow_sends_workflow_and_skips_chat(
        self, chat_service, mock_workflow_svc
    ):
        """initial_menu: next_workflow_id がある場合、次ワークフローを送信して chat() を呼ばないこと"""
        from domain.entities.workflow_definition import WorkflowDefinition, DisplayType, SelectionType
        next_def = WorkflowDefinition.model_validate({
            "id": "job_match_diagnosis",
            "name": "適職診断",
            "displayType": DisplayType.MODAL,
            "steps": [
                {
                    "id": 1,
                    "question": "Q",
                    "questionPrompt": "P",
                    "selectionType": SelectionType.SINGLE,
                    "options": [{"label": "Opt", "value": 1, "allowFreeText": False}],
                }
            ],
        })
        mock_workflow_svc.process_workflow_submission.return_value = (
            WorkflowPostProcessingResult(
                message="",
                next_agent_name="CareerAdvisor",
                next_workflow_id="job_match_diagnosis",
            ),
            [],
        )
        # get_definition は同期メソッドなので Mock（AsyncMock ではない）で上書き
        mock_workflow_svc.get_definition = Mock(return_value=next_def)

        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps({"workflow_id": "initial_menu", "answers": {"1": [{"value": 2}]}}),
            current_page=PageName.CHAT,
        )

        chat_service._toolcall_trace_message = {"type": "message", "role": "developer", "content": "trace"}

        responses = []
        with patch.object(chat_service, "chat", return_value=AsyncMock()) as mock_chat:
            mock_chat.return_value.__aiter__.return_value = []

            async for resp in chat_service.workflow_submitted(input_data, "127.0.0.1"):
                responses.append(resp)

        mock_chat.assert_not_called()
        assert len(responses) == 1
        assert responses[0].response_type == ChatResponseType.WORKFLOW
        mock_workflow_svc.get_definition.assert_called_with("job_match_diagnosis")

    @pytest.mark.asyncio
    async def test_workflow_submitted_initial_menu_create_session_db_error_propagates(
        self, chat_service, mock_workflow_svc, mock_chat_repo
    ):
        """initial_menu: create_chat_session が DB エラーを発生させた場合、例外が伝播すること"""
        mock_chat_repo.create_chat_session.side_effect = Exception("DB接続エラー")

        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps({"workflow_id": "initial_menu", "answers": {"1": [{"value": 1}]}}),
            current_page=PageName.CHAT,
        )

        with pytest.raises(Exception, match="DB接続エラー"):
            async for _ in chat_service.workflow_submitted(input_data, "127.0.0.1"):
                pass

    @pytest.mark.asyncio
    async def test_workflow_submitted_next_workflow_get_definition_fails_returns_error(
        self, chat_service, mock_workflow_svc
    ):
        """next_workflow_id の get_definition が ValueError を発生させた場合、エラーレスポンスを返すこと"""
        mock_workflow_svc.process_workflow_submission.return_value = (
            WorkflowPostProcessingResult(
                message="",
                next_agent_name="CareerAdvisor",
                next_workflow_id="job_match_diagnosis",
            ),
            [],
        )
        mock_workflow_svc.get_definition = Mock(side_effect=ValueError("定義ファイルが不正"))

        chat_service._toolcall_trace_message = {"type": "message", "role": "developer", "content": "trace"}

        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps({"workflow_id": "initial_menu", "answers": {"1": [{"value": 2}]}}),
            current_page=PageName.CHAT,
        )

        responses = []
        async for resp in chat_service.workflow_submitted(input_data, "127.0.0.1"):
            responses.append(resp)

        assert len(responses) == 1
        assert responses[0].response_type == ChatResponseType.ERROR


class TestApplyJobtypesAndUpdateAgents:
    """_apply_jobtypes_and_update_agents のテスト"""

    @pytest.mark.asyncio
    async def test_success_returns_none(self, chat_service, mock_position_svc):
        """update_jobtypes が tool_name を返し、ツール追加が成功した場合 None を返すテスト"""
        mock_position_svc.update_jobtypes = AsyncMock(
            return_value="search_job_postings_for_it_engineer"
        )

        with patch.object(
            chat_service, "_update_agents_with_position_search_tool", return_value=True
        ):
            result = await chat_service._apply_jobtypes_and_update_agents(
                ["システムエンジニア"], ChatRequestType.JOB_TYPES_SELECTED
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_no_tool_name_returns_error(self, chat_service, mock_position_svc):
        """update_jobtypes が None を返した場合、エラーレスポンスを返すテスト"""
        mock_position_svc.update_jobtypes = AsyncMock(return_value=None)

        with patch.object(
            chat_service, "_update_agents_with_position_search_tool"
        ) as mock_update:
            result = await chat_service._apply_jobtypes_and_update_agents(
                ["未サポート職種"], ChatRequestType.JOB_TYPES_SELECTED
            )
            mock_update.assert_not_called()

        assert result is not None
        assert result.response_type == ChatResponseType.ERROR
        assert result.message == "該当職種がまだサポートされていません。"

    @pytest.mark.asyncio
    async def test_tool_update_fails_returns_error(
        self, chat_service, mock_position_svc
    ):
        """_update_agents_with_position_search_tool が False を返した場合、エラーレスポンスを返すテスト"""
        mock_position_svc.update_jobtypes = AsyncMock(
            return_value="search_job_postings"
        )

        with patch.object(
            chat_service, "_update_agents_with_position_search_tool", return_value=False
        ):
            result = await chat_service._apply_jobtypes_and_update_agents(
                ["システムエンジニア"], ChatRequestType.JOB_TYPES_SELECTED
            )

        assert result is not None
        assert result.response_type == ChatResponseType.ERROR
        assert result.message == "求人検索ツールの設定に失敗しました。"


class TestWorkflowCancelled:
    """workflow_cancelledのテスト"""

    @pytest.mark.asyncio
    async def test_workflow_cancelled_success(self, chat_service, mock_workflow_svc):
        """ワークフローキャンセル時の正常系テスト"""
        mock_workflow_svc.exists_definition = Mock(return_value=True)
        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_CANCELLED,
            message=json.dumps({"workflow_id": "test_wf"}),
            current_page=PageName.CHAT,
        )

        with patch.object(chat_service, "chat", return_value=AsyncMock()) as mock_chat:
            mock_chat.return_value.__aiter__.return_value = []

            async for _ in chat_service.workflow_cancelled(input_data, "127.0.0.1"):
                pass

            mock_chat.assert_called_once()
            call_args = mock_chat.call_args[0][0]
            assert "test_wf" in call_args.message
            assert "中断" in call_args.message

    @pytest.mark.asyncio
    async def test_workflow_cancelled_invalid_json(self, chat_service):
        """ワークフローキャンセル時の不正なJSON入力テスト"""
        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_CANCELLED,
            message="invalid json",
            current_page=PageName.CHAT,
        )

        with patch.object(chat_service, "chat", return_value=AsyncMock()) as mock_chat:
            mock_chat.return_value.__aiter__.return_value = []

            async for _ in chat_service.workflow_cancelled(input_data, "127.0.0.1"):
                pass

            mock_chat.assert_called_once()
            call_args = mock_chat.call_args[0][0]
            assert "ワークフローを中断しました。" in call_args.message

    @pytest.mark.asyncio
    async def test_workflow_cancelled_unknown_id(self, chat_service, mock_workflow_svc):
        """未知のワークフローIDでのキャンセルテスト"""
        mock_workflow_svc.exists_definition = Mock(return_value=False)
        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_CANCELLED,
            message=json.dumps({"workflow_id": "unknown_wf"}),
            current_page=PageName.CHAT,
        )

        with patch.object(chat_service, "chat", return_value=AsyncMock()) as mock_chat:
            mock_chat.return_value.__aiter__.return_value = []

            async for _ in chat_service.workflow_cancelled(input_data, "127.0.0.1"):
                pass

            mock_chat.assert_called_once()
            call_args = mock_chat.call_args[0][0]
            assert "ユーザーがワークフローを中断しました。" in call_args.message

    @pytest.mark.asyncio
    async def test_workflow_cancelled_initial_menu_returns_error(self, chat_service):
        """initial_menu のキャンセルはエラーレスポンスを返し chat() が呼ばれないこと"""
        input_data = ChatRequestModel(
            request_type=ChatRequestType.WORKFLOW_CANCELLED,
            message=json.dumps({"workflow_id": "initial_menu"}),
            current_page=PageName.CHAT,
        )

        with patch.object(chat_service, "chat", return_value=AsyncMock()) as mock_chat:
            mock_chat.return_value.__aiter__.return_value = []

            responses = []
            async for resp in chat_service.workflow_cancelled(input_data, "127.0.0.1"):
                responses.append(resp)

        mock_chat.assert_not_called()
        assert len(responses) == 1
        assert responses[0].response_type == ChatResponseType.ERROR


class TestChatWorkflowTraversal:
    """START_WORKFLOWのパストラバーサル対策テスト"""

    @pytest.mark.asyncio
    async def test_start_workflow_traversal_attack(self, chat_service):
        """不正な形式のworkflow_idによるパストラバーサル攻撃を拒否すること"""
        # Runner.run_streamed をモックして、START_WORKFLOWツールコールをエミュレート
        raw_tool_call = SimpleNamespace(
            call_id="call-traversal",
            name=ToolName.START_WORKFLOW.value,
            arguments='{"WorkflowID": "../../etc/passwd"}',
        )

        events = [
            FakeStreamEvent(
                "run_item_stream_event", item=FakeToolCallItem(raw_tool_call)
            ),
        ]
        run_result = FakeRunResult(events)

        with (
            patch("services.chat_service.ToolCallItem", FakeToolCallItem),
            patch("services.chat_service.Runner.run_streamed", return_value=run_result),
            patch.object(chat_service, "_save_chat_history"),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            responses = []
            async for resp in chat_service.chat(
                ChatRequestModel(
                    request_type=ChatRequestType.CHAT,
                    current_page=PageName.CHAT,
                    message="workflow start",
                    current_message_id="msg-1",
                ),
                client_ip="127.0.0.1",
            ):
                responses.append(resp)

        # エラーレスポンスが返されることを確認
        assert any(r.response_type == ChatResponseType.ERROR for r in responses)
        # ファイルを開こうとしていないことを確認（FileNotFoundErrorが発生してキャッチされているはず）

    @pytest.mark.asyncio
    async def test_start_workflow_initial_menu_is_skipped(self, chat_service, mock_workflow_svc):
        """start_workflow に initial_menu が渡されても再表示されないこと"""
        chat_service._agents = {"CareerAdvisor": Mock(spec=Agent)}
        chat_service._active_agent_name = "CareerAdvisor"
        chat_service._conversation = {"MAIN": []}
        chat_service._chat_key = "MAIN"

        mock_chat_repo = chat_service._chat_repository
        mock_chat_repo.session_status.return_value = ChatSessionStatus.CHATTING
        mock_chat_repo.is_session_blocked.return_value = False
        chat_service.llm_output_guard.reset_session_for_new_response = Mock()
        chat_service.llm_output_guard.process_stream_chunk = Mock(return_value=[])
        chat_service.llm_output_guard.finalize_stream = Mock(return_value=[])
        chat_service.llm_output_guard.remove_session = Mock()

        raw_tool_call = SimpleNamespace(
            call_id="call-initial-menu",
            name=ToolName.START_WORKFLOW.value,
            arguments='{"WorkflowID": "initial_menu"}',
        )

        events = [
            FakeStreamEvent("run_item_stream_event", item=FakeToolCallItem(raw_tool_call)),
        ]
        run_result = FakeRunResult(events)

        with (
            patch("services.chat_service.ToolCallItem", FakeToolCallItem),
            patch("services.chat_service.Runner.run_streamed", return_value=run_result),
            patch.object(chat_service, "_save_chat_history"),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            responses = []
            async for resp in chat_service.chat(
                ChatRequestModel(
                    request_type=ChatRequestType.CHAT,
                    current_page=PageName.CHAT,
                    message="メニューを見せて",
                    current_message_id="msg-1",
                ),
                client_ip="127.0.0.1",
            ):
                responses.append(resp)

        # WORKFLOWレスポンスが返されないこと（ガードによりスキップ）
        assert not any(r.response_type == ChatResponseType.WORKFLOW for r in responses)
        # ワークフロー定義取得が呼ばれないこと
        mock_workflow_svc.get_definition.assert_not_called()


class TestChatSummaryIntegration:
    @pytest.mark.asyncio
    async def test_build_summary_context_uses_latest_completed(
        self, chat_service, mock_chat_repo
    ):
        summary_executor = Mock()
        latest_completed = Mock()
        latest_completed.summary_id = 1
        latest_completed.summary_text = '{"summary":"v1"}'
        latest_completed.summary_until_history_id = 100
        summary_executor.get_latest_completed.return_value = latest_completed
        history = Mock(spec=ChatHistory)
        history.id = 101
        summary_executor.get_histories_after.return_value = [history]

        chat_service._summary_service = summary_executor
        chat_service._chat_key = "MAIN"
        chat_service._toolcall_trace_message = {
            "type": "message",
            "role": LLMMessageRole.DEVELOPER,
            "content": "trace",
        }

        with patch.object(
            chat_service,
            "_convert_to_llm_messages",
            return_value=(
                {"MAIN": []},
                {
                    "MAIN": [
                        {"type": "message", "role": LLMMessageRole.USER, "content": "u"}
                    ]
                },
            ),
        ):
            await chat_service.build_summary_context("session-1")

        summary_executor.get_latest_completed.assert_called_once_with("session-1")
        summary_executor.get_histories_after.assert_called_once_with("session-1", 100)
        mock_chat_repo.get_main_chat_histories.assert_not_called()
        assert (
            chat_service._conversation["MAIN"][0]
            == chat_service._toolcall_trace_message
        )
        assert chat_service._conversation["MAIN"][1]["role"] == LLMMessageRole.DEVELOPER

    @pytest.mark.asyncio
    async def test_build_summary_context_fallbacks_without_completed(
        self, chat_service, mock_chat_repo
    ):
        summary_executor = Mock()
        summary_executor.get_latest_completed.return_value = None
        history = Mock(spec=ChatHistory)
        history.id = 1
        mock_chat_repo.get_main_chat_histories.return_value = [history]

        chat_service._summary_service = summary_executor
        chat_service._chat_key = "MAIN"
        chat_service._toolcall_trace_message = {
            "type": "message",
            "role": LLMMessageRole.DEVELOPER,
            "content": "trace",
        }

        with patch.object(
            chat_service,
            "_convert_to_llm_messages",
            return_value=(
                {"MAIN": []},
                {
                    "MAIN": [
                        {"type": "message", "role": LLMMessageRole.USER, "content": "u"}
                    ]
                },
            ),
        ):
            await chat_service.build_summary_context("session-1")

        mock_chat_repo.get_main_chat_histories.assert_called_once()
        summary_executor.get_histories_after.assert_not_called()

    @pytest.mark.asyncio
    async def test_build_summary_context_appends_incremental_histories_when_summary_unchanged(
        self, chat_service, mock_chat_repo
    ):
        summary_executor = Mock()
        latest_completed = Mock()
        latest_completed.summary_id = 1
        latest_completed.summary_text = '{"summary":"v1"}'
        latest_completed.summary_until_history_id = 100
        summary_executor.get_latest_completed.return_value = latest_completed

        first_history = Mock(spec=ChatHistory)
        first_history.id = 101
        second_history = Mock(spec=ChatHistory)
        second_history.id = 102
        summary_executor.get_histories_after.side_effect = [
            [first_history],
            [second_history],
        ]

        chat_service._summary_service = summary_executor
        chat_service._chat_key = "MAIN"
        chat_service._toolcall_trace_message = {
            "type": "message",
            "role": LLMMessageRole.DEVELOPER,
            "content": "trace",
        }

        with patch.object(
            chat_service,
            "_convert_to_llm_messages",
            side_effect=[
                (
                    {"MAIN": [first_history]},
                    {
                        "MAIN": [
                            {
                                "type": "message",
                                "role": LLMMessageRole.USER,
                                "content": "u1",
                            }
                        ]
                    },
                ),
                (
                    {"MAIN": [second_history]},
                    {
                        "MAIN": [
                            {
                                "type": "message",
                                "role": LLMMessageRole.USER,
                                "content": "u2",
                            }
                        ]
                    },
                ),
            ],
        ):
            await chat_service.build_summary_context("session-1")
            await chat_service.build_summary_context("session-1")

        # 2回目はフル再構築ではなく、前回last_history_id以降の差分のみ追加
        assert summary_executor.get_histories_after.call_count == 2
        summary_executor.get_histories_after.assert_any_call("session-1", 100)
        summary_executor.get_histories_after.assert_any_call("session-1", 101)
        assert [m.get("content") for m in chat_service._conversation["MAIN"][-2:]] == [
            "u1",
            "u2",
        ]

    @pytest.mark.asyncio
    async def test_chat_calls_summary_check_after_success(
        self, chat_service, mock_chat_repo
    ):
        TestChatStreamingCompatibility._prepare_chat_service_for_chat(
            chat_service, mock_chat_repo
        )
        summary_executor = Mock()
        summary_executor.get_latest_completed.return_value = None
        chat_service._summary_service = summary_executor
        chat_service._toolcall_trace_message = {
            "type": "message",
            "role": LLMMessageRole.DEVELOPER,
            "content": "trace",
        }
        mock_chat_repo.get_main_chat_histories.return_value = []
        run_result = FakeRunResult(
            [],
            last_agent_name="CareerAdvisor",
            last_response_id="resp-next",
        )

        with (
            patch("services.chat_service.Runner.run_streamed", return_value=run_result),
            patch.object(chat_service, "_save_chat_history"),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            _ = [
                chunk
                async for chunk in chat_service.chat(
                    ChatRequestModel(
                        request_type=ChatRequestType.CHAT,
                        current_page=PageName.CHAT,
                        message="こんにちは",
                        current_message_id="msg-summary-1",
                    ),
                    client_ip="127.0.0.1",
                )
            ]

        summary_executor.check_should_start_summary.assert_called_once_with(
            "test-session-id"
        )


def test_json_default_and_fallback_paths(chat_service):
    @dataclass
    class Data:
        value: int

    class HasModelDump:
        def model_dump(self):
            return {"model": True}

    class HasDictMethod:
        def dict(self):
            return {"dict": True}

    class HasDictAttr:
        def __init__(self):
            self.answer = 42

    class Fallback:
        __slots__ = ()

    fallback = Fallback()

    assert chat_service._serialize_tool_output_for_storage("raw") == "raw"
    assert json.loads(chat_service._serialize_tool_output_for_storage(Data(1))) == {
        "value": 1
    }
    assert json.loads(
        chat_service._serialize_tool_output_for_storage(HasModelDump())
    ) == {"model": True}
    assert json.loads(
        chat_service._serialize_tool_output_for_storage(HasDictMethod())
    ) == {"dict": True}
    assert json.loads(
        chat_service._serialize_tool_output_for_storage(HasDictAttr())
    ) == {"answer": 42}
    assert chat_service._serialize_tool_output_for_storage(fallback) == json.dumps(
        str(fallback),
        ensure_ascii=False,
    )


def test_convert_to_llm_messages_covers_all_branches(chat_service):
    chat_service._position_id = 1
    position_guide = Mock()
    position_guide.clone.return_value = Mock()
    chat_service._agents[AgentName.POSITION_GUIDE] = position_guide

    histories = [
        ChatHistory(
            session_id="sess",
            position_id=None,
            active_agent=AgentName.CAREER_ADVISOR,
            message_id="u1",
            role=LLMMessageRole.USER,
            content="user",
        ),
        ChatHistory(
            session_id="sess",
            position_id=None,
            active_agent=AgentName.CAREER_ADVISOR,
            message_id="a1",
            role=LLMMessageRole.ASSISTANT,
            content="assistant",
        ),
        ChatHistory(
            session_id="sess",
            position_id=None,
            active_agent=AgentName.CAREER_ADVISOR,
            message_id="t0",
            role=LLMMessageRole.TOOL,
            content="",
            tool_call_id="call-empty",
            tool_name=ToolName.GENERIC_POSITION_SEARCH.value,
            tool_input={"foo": 1},
        ),
        ChatHistory(
            session_id="sess",
            position_id=1,
            active_agent=AgentName.POSITION_GUIDE,
            message_id="t1",
            role=LLMMessageRole.TOOL,
            content='{"AllPositionIds":["1","2"]}',
            tool_call_id="call-pos",
            tool_name=ToolName.GENERIC_POSITION_SEARCH.value,
            tool_input={"foo": 2},
        ),
        ChatHistory(
            session_id="sess",
            position_id=None,
            active_agent=AgentName.CAREER_ADVISOR,
            message_id="t2",
            role=LLMMessageRole.TOOL,
            content='{"Jobtypes":["A"]}',
            tool_call_id="call-job",
            tool_name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS.value,
            tool_input={"foo": 3},
        ),
        ChatHistory(
            session_id="sess",
            position_id=None,
            active_agent=AgentName.CAREER_ADVISOR,
            message_id="r1",
            role=LLMMessageRole.REASONING,
            content="reasoning",
        ),
        ChatHistory(
            session_id="sess",
            position_id=None,
            active_agent=AgentName.CAREER_ADVISOR,
            message_id="x1",
            role="unsupported",
            content="ignore",
        ),
    ]

    with (
        patch.object(
            chat_service,
            "_parse_tool_output",
            side_effect=[
                {"AllPositionIds": ["1", "2"]},
                {"Jobtypes": ["A"]},
            ],
        ),
        patch.object(
            chat_service,
            "_generate_position_search_fake_result",
            return_value="fake-position",
        ) as mock_generate_fake_result,
        patch.object(
            chat_service,
            "_process_jobtype_search_result",
            return_value={"Jobtypes": ["A"]},
        ) as mock_process_jobtypes,
        patch.object(chat_service.logger, "warning") as mock_warning,
        patch.object(chat_service.logger, "error") as mock_error,
    ):
        chat_histories, all_messages = chat_service._convert_to_llm_messages(histories)

    assert "1" in chat_histories
    assert len(chat_histories[MAIN_CHAT_KEY]) >= 5
    assert any(
        isinstance(message, dict)
        and message.get("type") == "function_call_output"
        and message.get("output") == "ツール実行結果がまだありません。"
        for message in all_messages[MAIN_CHAT_KEY]
    )
    mock_generate_fake_result.assert_called_once_with(2)
    mock_process_jobtypes.assert_called_once()
    assert mock_warning.called
    assert mock_error.called
    position_guide.clone.assert_called_once()


def test_extract_helpers_and_position_agent_paths(chat_service):
    assert chat_service._extract_position_search_tool_name(None) is None
    assert chat_service._extract_position_search_tool_name({"ToolName": "  "}) is None
    assert (
        chat_service._extract_position_search_tool_name({"ToolName": " search "})
        == "search"
    )

    with patch.object(chat_service.logger, "warning") as mock_warning:
        assert chat_service._extract_selected_jobtypes(None) == []
        assert chat_service._extract_selected_jobtypes({"SearchFilters": []}) == []
        assert (
            chat_service._extract_selected_jobtypes({"SearchFilters": {"Jobtypes": []}})
            == []
        )
        assert (
            chat_service._extract_selected_jobtypes(
                {"SearchFilters": {"Jobtypes": {"A": {"Value": "x", "Selected": True}}}}
            )
            == []
        )
        assert chat_service._extract_selected_jobtypes(
            {
                "SearchFilters": {
                    "Jobtypes": {
                        "A": [
                            {"Value": " IT ", "Selected": True},
                            {"Value": "IT", "Selected": True},
                            {"Value": "Sales", "Selected": False},
                            "bad",
                        ],
                        "B": [{"Value": "Finance", "Selected": True}],
                    }
                }
            }
        ) == ["IT", "Finance"]
    assert mock_warning.call_count >= 1

    chat_service._agents.clear()
    position_guide = Mock()
    position_guide.clone.return_value = "cloned"
    chat_service._agents = {AgentName.POSITION_GUIDE: position_guide}
    chat_service._create_position_agent_if_not_exist("position-1")
    assert chat_service._agents["position-1"] == "cloned"

    chat_service._create_position_agent_if_not_exist("position-1")
    assert chat_service._agents["position-1"] == "cloned"


@pytest.mark.asyncio
async def test_history_lookup_helpers_cover_decrypt_and_format_paths(chat_service):
    chat_service._chat_repository.has_position_chat_histories.return_value = True
    chat_service._chat_repository.get_main_chat_histories.return_value = []
    chat_service._chat_repository.get_position_detail_chat_histories.return_value = []

    with patch("services.chat_service.decrypt", return_value="real-pos"):
        assert await chat_service.check_if_previous_chat_histories_exist("encrypted") is True
        assert await chat_service.load_previous_chat_histories(5, "encrypted", "before") == (
            [],
            True,
        )


@pytest.mark.asyncio
async def test_handle_security_detection_covers_forbidden_and_unexpected(chat_service):
    chat_response = Mock()
    chat_response.create_error_response.return_value = "error"
    chat_service._chat_repository.block_session = Mock()
    chat_service.llm_output_guard.remove_session = Mock()

    class FakeForbiddenWordDetectedException(Exception):
        def __init__(self, word: str):
            super().__init__(word)
            self.word = word

    with patch(
        "services.chat_service.ForbiddenWordDetectedException",
        FakeForbiddenWordDetectedException,
    ):
        result = await chat_service._handle_security_detection(
            FakeForbiddenWordDetectedException("bad"),
            "session-1",
            ChatSessionStatus.CHATTING,
            chat_response,
            "stream",
        )

    assert result == "error"
    chat_service._chat_repository.block_session.assert_called_once()
    chat_service.llm_output_guard.remove_session.assert_called_with("session-1")

    with pytest.raises(RuntimeError):
        await chat_service._handle_security_detection(
            RuntimeError("boom"),
            "session-2",
            ChatSessionStatus.CHATTING,
            chat_response,
        )


@pytest.mark.pre_extraction_parity
@pytest.mark.asyncio
async def test_build_summary_context_returns_early_when_no_summary_service(chat_service):
    chat_service._summary_service = None
    chat_service._chat_key = MAIN_CHAT_KEY
    await chat_service.build_summary_context("any-session")


@pytest.mark.pre_extraction_parity
@pytest.mark.asyncio
async def test_build_summary_context_returns_early_when_not_main_chat_key(chat_service):
    chat_service._summary_service = Mock()
    chat_service._chat_key = "position-chat"
    await chat_service.build_summary_context("any-session")
    chat_service._summary_service.get_latest_completed.assert_not_called()


@pytest.mark.pre_extraction_parity
def test_find_last_non_position_guide_agent_skips_position_guide_entries(chat_service):
    guide_history = Mock(spec=ChatHistory)
    guide_history.active_agent = AgentName.POSITION_GUIDE
    default_history = Mock(spec=ChatHistory)
    default_history.active_agent = "CareerAdvisor"
    chat_service._chat_histories[MAIN_CHAT_KEY] = [default_history, guide_history]
    result = chat_service._find_last_non_position_guide_agent()
    assert result == "CareerAdvisor"
