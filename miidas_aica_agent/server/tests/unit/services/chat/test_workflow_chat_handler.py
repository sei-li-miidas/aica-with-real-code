"""WorkflowChatHandler unit tests — 100% branch coverage.

Branch inventory
----------------
prepare_job_type_decided:
  - B3: JSON decode error → error_response
  - B4: jobtypes is list → filter and strip
  - B5: jobtypes is not list → set to None
  - B6: jobtypes is empty (falsy) → error_response
  - B7: tool_name is None/empty → error_response
  - B8: _update_agents returns False → error_response
  - B9: success → prepared_message

prepare_clear_jobtype:
  - B10: success (always) → prepared_message

prepare_workflow_submitted:
  - B11: JSON decode error → error_response
  - B12: TypeError → error_response
  - B13: not workflow_id → error_response
  - B14: answers not dict → error_response
  - B15: ValueError from process_workflow_submission → error_response
  - B16: FileNotFoundError from process_workflow_submission → error_response
  - B17: history_to_save is empty → result.workflow_histories == []
  - B18: history_to_save non-empty, active_agent is set → result.workflow_histories に正しい histories が含まれる
  - B19: history_to_save non-empty, active_agent is None/empty → AgentName.CAREER_ADVISOR が使われる
  - B-NEW1: workflow_id == INITIAL_MENU_WORKFLOW_ID → create_session が呼ばれる
  - B-NEW1-ERR: INITIAL_MENU で create_session が例外を上げた場合、例外が伝播すること
  - B-NEW2: INITIAL_MENU 以外 → create_session が呼ばれない
  - B-NEW3: post_result.next_agent_name が result.next_agent_name に反映される
  - B-NEW4: result.workflow_id に処理した workflow_id が入る
  - B-NEW5: post_result.next_workflow_id がある場合 result.next_workflow_id_response が非 None
  - B-NEW9: payload の extra が process_workflow_submission に転送される
  - B-NEW10: payload に extra が無い場合 None が転送される
  - B-NEW11: history entry に message_id_suffix がある場合、message_id に suffix が挿入される
  - B-NEW12: message_id_suffix が無い entry は従来通りの message_id 形式になる
  - B-NEW13: INITIAL_MENU 以外で next_agent_name が設定されていても、ChatHistory.active_agent は
             現在の active_agent（get_active_agent_name()）が使われる
  - B-NEW14: INITIAL_MENU では ChatHistory.active_agent に next_agent_name が使われる

prepare_workflow_submitted (selected_jobtypes path):
  - B20: selected_jobtypes non-empty, update_jobtypes returns empty → error_response
  - B21: selected_jobtypes non-empty, _update_agents fails → error_response
  - B22: selected_jobtypes non-empty, success → prepared_message from post_result.message
  - B-NEW6: selected_jobtypes エラー時も result.workflow_histories にエントリが含まれる

prepare_workflow_cancelled:
  - B23: JSON decode error → fallback message with "ワークフロー"
  - B24: TypeError → fallback message with "ワークフロー"
  - B25: workflow_id is empty → fallback message with "ワークフロー"
  - B26: exists_definition returns False → fallback message with "ワークフロー"
  - B27: workflow_id present and exists → message with "ワークフロー `<id>`"
  - B-NEW7: workflow_id == INITIAL_MENU_WORKFLOW_ID → error_response が返る
  - B-NEW8: INITIAL_MENU 以外の cancel は従来通り error_response is None

_update_agents_with_position_search_tool:
  - B28: updated_agents is empty/falsy → return False
  - B29: tool_name not None, configured_tool_name != tool_name → return False
  - B30: tool_name not None, configured_tool_name == tool_name → return True
  - B31: tool_name is None → skip name check, return True
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


pytestmark = pytest.mark.pre_extraction_parity
from services.chat.workflow_chat_handler import WorkflowChatHandler
from services.llm_service import AgentName
from services.workflow_handlers.base import WorkflowPostProcessingResult
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import ChatResponseType
from utils.enum import LLMMessageRole, PageName, ToolName
from utils.log_utils import clear_session_id, set_session_id


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _set_session_id():
    """Ensure a valid session_id ContextVar is set for all tests in this module."""
    set_session_id("test-session-workflow-handler")
    yield
    clear_session_id()


def _make_handler(
    position_service=None,
    workflow_service=None,
    llm_service=None,
    create_session=None,
    agents=None,
    provider="gpt-4o",
    active_agent_name="CareerAdvisor",
):
    """Build a WorkflowChatHandler with sensible defaults."""
    if position_service is None:
        position_service = MagicMock()
    if workflow_service is None:
        workflow_service = MagicMock()
    if llm_service is None:
        llm_service = MagicMock()
    if create_session is None:
        create_session = MagicMock()
    if agents is None:
        agents = {"CareerAdvisor": (MagicMock(), True)}

    return WorkflowChatHandler(
        position_service=position_service,
        workflow_service=workflow_service,
        llm_service=llm_service,
        create_session=create_session,
        get_agents=lambda: agents,
        get_provider=lambda: provider,
        get_active_agent_name=lambda: active_agent_name,
    )


def _make_request(
    request_type: ChatRequestType = ChatRequestType.JOB_TYPES_SELECTED,
    message: str = "[]",
    message_id: str = "msg-test-001",
) -> ChatRequestModel:
    return ChatRequestModel(
        request_type=request_type,
        current_page=PageName.CHAT,
        message=message,
        current_message_id=message_id,
    )


# ---------------------------------------------------------------------------
# prepare_job_type_decided tests
# ---------------------------------------------------------------------------


class TestPrepareJobTypeDecided:
    @pytest.mark.asyncio
    async def test_json_decode_error_returns_error_response(self):
        """B3: Invalid JSON → error_response."""
        handler = _make_handler()
        request = _make_request(message="{invalid")
        result = await handler.prepare_job_type_decided(request)
        assert result.error_response is not None
        assert result.error_response.response_type == ChatResponseType.ERROR
        assert result.error_response.message == "不正なJSON形式です"

    @pytest.mark.asyncio
    async def test_valid_list_filters_empty_strings(self):
        """B4: list input → filter/strip, then success."""
        agents = {"CareerAdvisor": (MagicMock(), True)}
        llm_svc = MagicMock()
        llm_svc.update_agent_by_tool_name.return_value = (agents, "search_tool")
        pos_svc = MagicMock()
        pos_svc.update_jobtypes = AsyncMock(return_value="search_tool")
        handler = _make_handler(
            position_service=pos_svc, llm_service=llm_svc, agents=agents
        )
        # Include empty strings that should be stripped out (only one valid entry remains)
        request = _make_request(message=json.dumps(["エンジニア", "", "  "]))
        result = await handler.prepare_job_type_decided(request)
        assert result.error_response is None
        assert "エンジニア" in result.prepared_message

    @pytest.mark.asyncio
    async def test_non_list_input_is_treated_as_empty(self):
        """B5 + B6: dict input is not a list → jobtypes=None → error_response."""
        handler = _make_handler()
        request = _make_request(message=json.dumps({"jobtypes": ["x"]}))
        result = await handler.prepare_job_type_decided(request)
        assert result.error_response is not None
        assert result.error_response.message == "職種が選択されていない"

    @pytest.mark.asyncio
    async def test_empty_list_returns_error_response(self):
        """B6: Empty list (after filtering) → error_response."""
        handler = _make_handler()
        request = _make_request(message=json.dumps(["", "   "]))
        result = await handler.prepare_job_type_decided(request)
        assert result.error_response is not None
        assert result.error_response.message == "職種が選択されていない"

    @pytest.mark.asyncio
    async def test_update_jobtypes_returns_none_returns_error(self):
        """B7: update_jobtypes returns None → error_response."""
        pos_svc = MagicMock()
        pos_svc.update_jobtypes = AsyncMock(return_value=None)
        handler = _make_handler(position_service=pos_svc)
        request = _make_request(message=json.dumps(["エンジニア"]))
        result = await handler.prepare_job_type_decided(request)
        assert result.error_response is not None
        assert result.error_response.message == "該当職種がまだサポートされていません。"

    @pytest.mark.asyncio
    async def test_agent_update_fails_returns_error(self):
        """B8: _update_agents returns False → error_response."""
        pos_svc = MagicMock()
        pos_svc.update_jobtypes = AsyncMock(return_value="search_tool")
        llm_svc = MagicMock()
        # empty dict → falsy → _update_agents returns False
        llm_svc.update_agent_by_tool_name.return_value = ({}, "search_tool")
        handler = _make_handler(position_service=pos_svc, llm_service=llm_svc)
        request = _make_request(message=json.dumps(["エンジニア"]))
        result = await handler.prepare_job_type_decided(request)
        assert result.error_response is not None
        assert result.error_response.message == "求人検索ツールの設定に失敗しました。"

    @pytest.mark.asyncio
    async def test_success_returns_prepared_message(self):
        """B9: All checks pass → prepared_message with jobtype name."""
        agents = {"CareerAdvisor": (MagicMock(), True)}
        pos_svc = MagicMock()
        pos_svc.update_jobtypes = AsyncMock(return_value="search_tool")
        llm_svc = MagicMock()
        llm_svc.update_agent_by_tool_name.return_value = (agents, "search_tool")
        handler = _make_handler(
            position_service=pos_svc, llm_service=llm_svc, agents=agents
        )
        request = _make_request(message=json.dumps(["エンジニア"]))
        result = await handler.prepare_job_type_decided(request)
        assert result.error_response is None
        assert "エンジニア" in result.prepared_message


# ---------------------------------------------------------------------------
# prepare_clear_jobtype tests
# ---------------------------------------------------------------------------


class TestPrepareClearJobtype:
    @pytest.mark.asyncio
    async def test_clear_jobtype_calls_clear_and_returns_message(self):
        """B10: clear_jobtypes called; update_agents called with None,None; message returned."""
        agents = {"CareerAdvisor": (MagicMock(), True)}
        pos_svc = MagicMock()
        pos_svc.clear_jobtypes = AsyncMock()
        llm_svc = MagicMock()
        llm_svc.update_agent_by_tool_name.return_value = (agents, None)
        handler = _make_handler(
            position_service=pos_svc, llm_service=llm_svc, agents=agents
        )
        request = _make_request(
            request_type=ChatRequestType.JOB_TYPES_CLEAR, message="{}"
        )
        result = await handler.prepare_clear_jobtype(request)
        pos_svc.clear_jobtypes.assert_awaited_once()
        llm_svc.update_agent_by_tool_name.assert_called_once()
        assert result.error_response is None
        assert "職種" in result.prepared_message


# ---------------------------------------------------------------------------
# prepare_workflow_submitted tests
# ---------------------------------------------------------------------------


class TestPrepareWorkflowSubmitted:
    @pytest.mark.asyncio
    async def test_json_decode_error_returns_error(self):
        """B11: Invalid JSON → error_response."""
        handler = _make_handler()
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message="{invalid",
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.error_response is not None
        assert result.error_response.message == "不正なJSON形式です"

    @pytest.mark.asyncio
    async def test_type_error_returns_error(self):
        """B12: Non-dict payload (None) → AttributeError from None.get() → error_response."""
        handler = _make_handler()
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message="null",
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.error_response is not None
        assert result.error_response.message == "不正なJSON形式です"

    @pytest.mark.asyncio
    async def test_missing_workflow_id_returns_error(self):
        """B13: workflow_id empty string → error_response."""
        handler = _make_handler()
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps({"workflow_id": "", "answers": {"1": [{"value": 1}]}}),
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.error_response is not None
        assert (
            result.error_response.message
            == "ワークフローIDが存在しない、または不正な回答形式です"
        )

    @pytest.mark.asyncio
    async def test_answers_not_dict_returns_error(self):
        """B14: answers is list not dict → error_response."""
        handler = _make_handler()
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps({"workflow_id": "wf-1", "answers": [1, 2, 3]}),
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.error_response is not None
        assert (
            result.error_response.message
            == "ワークフローIDが存在しない、または不正な回答形式です"
        )

    @pytest.mark.asyncio
    async def test_value_error_from_service_returns_error(self):
        """B15: ValueError from process_workflow_submission → error_response."""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            side_effect=ValueError("bad answers")
        )
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-1", "answers": {"1": [{"value": 1}]}}
            ),
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.error_response is not None
        assert result.error_response.message == "bad answers"

    @pytest.mark.asyncio
    async def test_file_not_found_error_from_service_returns_error(self):
        """B16: FileNotFoundError → specific error message."""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            side_effect=FileNotFoundError("missing")
        )
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-1", "answers": {"1": [{"value": 1}]}}
            ),
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.error_response is not None
        assert result.error_response.message == "ワークフロー定義が見つかりません: wf-1"

    @pytest.mark.asyncio
    async def test_empty_history_to_save_skips_save(self):
        """B17: history_to_save is empty list → result.workflow_histories == []."""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(WorkflowPostProcessingResult(message="続けます。"), [])
        )
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-1", "answers": {"1": [{"value": 1}]}}
            ),
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.error_response is None
        assert result.prepared_message == "続けます。"
        assert result.workflow_histories == []

    @pytest.mark.asyncio
    async def test_non_empty_history_with_active_agent_saves_histories(self):
        """B18: history_to_save non-empty, active_agent is set → result.workflow_histories に正しい histories が含まれる。"""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(message="回答ありがとうございました。"),
                [
                    {"role": "user", "content": "Q1"},
                    {"role": "assistant", "content": "A1"},
                ],
            )
        )
        handler = _make_handler(
            workflow_service=workflow_svc,
            active_agent_name="CareerAdvisor",
        )
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-2", "answers": {"1": [{"value": 1}]}}
            ),
        )
        with patch(
            "services.chat.workflow_chat_handler.get_session_id",
            return_value="sess-001",
        ):
            result = await handler.prepare_workflow_submitted(request)

        assert result.error_response is None
        assert len(result.workflow_histories) == 2
        assert all(h.message_id.startswith("wf_wf-2_") for h in result.workflow_histories)
        assert len({h.message_id for h in result.workflow_histories}) == 2
        assert result.workflow_histories[0].active_agent == "CareerAdvisor"

    @pytest.mark.asyncio
    async def test_non_empty_history_without_active_agent_uses_default(self):
        """B19: history_to_save non-empty, active_agent is None/empty → AgentName.CAREER_ADVISOR が使われる。"""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(message="回答ありがとうございました。"),
                [{"role": "user", "content": "Q1"}],
            )
        )
        # active_agent_name="" (falsy) → should fallback to AgentName.CAREER_ADVISOR
        handler = _make_handler(
            workflow_service=workflow_svc,
            active_agent_name="",
        )
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-3", "answers": {"1": [{"value": 1}]}}
            ),
        )
        with patch(
            "services.chat.workflow_chat_handler.get_session_id",
            return_value="sess-002",
        ):
            result = await handler.prepare_workflow_submitted(request)

        assert result.error_response is None
        assert len(result.workflow_histories) == 1
        assert result.workflow_histories[0].active_agent == AgentName.CAREER_ADVISOR

    @pytest.mark.asyncio
    async def test_extra_field_is_forwarded_to_process_workflow_submission(self):
        """B-NEW9: payload の extra が process_workflow_submission に転送される。"""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(WorkflowPostProcessingResult(message="ok"), [])
        )
        handler = _make_handler(workflow_service=workflow_svc)
        extra_payload = {"summary": "転職軸まとめ", "explanation": "解説"}
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {
                    "workflow_id": "position_change_analyze",
                    "answers": {"5": [{"value": 1}]},
                    "extra": extra_payload,
                }
            ),
        )
        await handler.prepare_workflow_submitted(request)

        workflow_svc.process_workflow_submission.assert_awaited_once_with(
            "position_change_analyze",
            {"5": [{"value": 1}]},
            extra=extra_payload,
        )

    @pytest.mark.asyncio
    async def test_missing_extra_field_forwards_none(self):
        """B-NEW10: payload に extra が無い場合 None が転送される。"""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(WorkflowPostProcessingResult(message="ok"), [])
        )
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps({"workflow_id": "wf-x", "answers": {"1": [{"value": 1}]}}),
        )
        await handler.prepare_workflow_submitted(request)

        workflow_svc.process_workflow_submission.assert_awaited_once_with(
            "wf-x",
            {"1": [{"value": 1}]},
            extra=None,
        )

    @pytest.mark.asyncio
    async def test_history_entry_with_message_id_suffix_is_inserted(self):
        """B-NEW11: history entry に message_id_suffix がある場合、message_id に suffix が挿入される。"""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(message="ok"),
                [
                    {
                        "role": "assistant",
                        "content": "転職軸をまとめました",
                        "message_id_suffix": "summary",
                    },
                    {"role": "user", "content": "求人を探す"},
                ],
            )
        )
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "position_change_analyze", "answers": {"5": [{"value": 1}]}}
            ),
        )
        with patch(
            "services.chat.workflow_chat_handler.get_session_id",
            return_value="sess-summary",
        ):
            result = await handler.prepare_workflow_submitted(request)

        suffixed, plain = result.workflow_histories
        assert suffixed.message_id.startswith("wf_position_change_analyze_summary_")
        assert plain.message_id.startswith("wf_position_change_analyze_")
        assert "_summary_" not in plain.message_id

    @pytest.mark.asyncio
    async def test_history_entry_without_suffix_uses_default_message_id_format(self):
        """B-NEW12: message_id_suffix が無い entry は従来通りの message_id 形式になる。"""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(message="ok"),
                [{"role": "user", "content": "回答"}],
            )
        )
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps({"workflow_id": "wf-y", "answers": {"1": [{"value": 1}]}}),
        )
        with patch(
            "services.chat.workflow_chat_handler.get_session_id",
            return_value="sess-plain",
        ):
            result = await handler.prepare_workflow_submitted(request)

        assert result.workflow_histories[0].message_id.startswith("wf_wf-y_")

    @pytest.mark.asyncio
    async def test_non_initial_menu_history_uses_current_active_agent_not_next(self):
        """B-NEW13: INITIAL_MENU 以外で next_agent_name が設定されていても、
        ChatHistory.active_agent には現在の active_agent（get_active_agent_name()）が使われる。
        """
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(
                    message="", next_agent_name="CareerAdvisor"
                ),
                [{"role": "user", "content": "求人を探す"}],
            )
        )
        handler = _make_handler(
            workflow_service=workflow_svc,
            active_agent_name="PositionChangeAnalyze",
        )
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "position_change_analyze", "answers": {"5": [{"value": 1}]}}
            ),
        )
        result = await handler.prepare_workflow_submitted(request)

        assert result.workflow_histories[0].active_agent == "PositionChangeAnalyze"
        assert result.next_agent_name == "CareerAdvisor"

    @pytest.mark.asyncio
    async def test_initial_menu_history_uses_next_agent_name(self):
        """B-NEW14: INITIAL_MENU では ChatHistory.active_agent に next_agent_name が使われる。"""
        from utils.const import INITIAL_MENU_WORKFLOW_ID

        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(
                    message="", next_agent_name="PositionChangeAnalyze"
                ),
                [{"role": "user", "content": "転職理由診断"}],
            )
        )
        handler = _make_handler(
            workflow_service=workflow_svc,
            # active_agent_name はまだ設定されていない想定（initial_menu 実行時の状態）
            active_agent_name="",
        )
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": INITIAL_MENU_WORKFLOW_ID, "answers": {"1": [{"value": 3}]}}
            ),
        )
        result = await handler.prepare_workflow_submitted(request)

        assert result.workflow_histories[0].active_agent == "PositionChangeAnalyze"

    @pytest.mark.asyncio
    async def test_selected_jobtypes_update_jobtypes_empty_returns_error(self):
        """B20: selected_jobtypes non-empty, update_jobtypes returns empty → error_response."""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(
                    message="診断完了", selected_jobtypes=["エンジニア"]
                ),
                [],
            )
        )
        position_svc = MagicMock()
        position_svc.update_jobtypes = AsyncMock(return_value=None)
        handler = _make_handler(
            workflow_service=workflow_svc, position_service=position_svc
        )
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-sel", "answers": {"1": [{"value": 1}]}}
            ),
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.error_response is not None
        assert result.error_response.message == "該当職種がまだサポートされていません。"
        position_svc.update_jobtypes.assert_awaited_once_with(["エンジニア"])

    @pytest.mark.asyncio
    async def test_selected_jobtypes_failure_keeps_history_persisted(self):
        """B-NEW6: selected_jobtypes 更新失敗時でも result.workflow_histories にエントリが含まれる（DB 保存はサービス側が担う）。"""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(
                    message="診断完了", selected_jobtypes=["エンジニア"]
                ),
                [{"role": "user", "content": "Q1"}],
            )
        )
        position_svc = MagicMock()
        position_svc.update_jobtypes = AsyncMock(return_value=None)
        handler = WorkflowChatHandler(
            position_service=position_svc,
            workflow_service=workflow_svc,
            llm_service=MagicMock(),
            get_agents=lambda: {"CareerAdvisor": (MagicMock(), True)},
            get_provider=lambda: "gpt-4o",
            create_session=MagicMock(),
            get_active_agent_name=lambda: "CareerAdvisor",
        )
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-sel", "answers": {"1": [{"value": 1}]}}
            ),
        )

        with patch(
            "services.chat.workflow_chat_handler.get_session_id",
            return_value="sess-003",
        ):
            result = await handler.prepare_workflow_submitted(request)

        assert result.error_response is not None
        assert len(result.workflow_histories) == 1

    @pytest.mark.asyncio
    async def test_selected_jobtypes_update_agents_fails_returns_error(self):
        """B21: selected_jobtypes non-empty, _update_agents fails → error_response."""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(
                    message="診断完了", selected_jobtypes=["エンジニア"]
                ),
                [],
            )
        )
        position_svc = MagicMock()
        position_svc.update_jobtypes = AsyncMock(return_value="search_tool_v1")
        llm_svc = MagicMock()
        llm_svc.update_agent_by_tool_name.return_value = ({}, "search_tool_v1")
        handler = _make_handler(
            workflow_service=workflow_svc,
            position_service=position_svc,
            llm_service=llm_svc,
        )
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-sel", "answers": {"1": [{"value": 1}]}}
            ),
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.error_response is not None
        assert result.error_response.message == "求人検索ツールの設定に失敗しました。"

    @pytest.mark.asyncio
    async def test_selected_jobtypes_success_returns_message(self):
        """B22: selected_jobtypes non-empty, success → prepared_message from post_result.message."""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(
                    message="診断完了", selected_jobtypes=["エンジニア"]
                ),
                [],
            )
        )
        position_svc = MagicMock()
        position_svc.update_jobtypes = AsyncMock(return_value="search_tool_v1")
        agents = {"CareerAdvisor": (MagicMock(), True)}
        llm_svc = MagicMock()
        llm_svc.update_agent_by_tool_name.return_value = (agents, "search_tool_v1")
        handler = _make_handler(
            workflow_service=workflow_svc,
            position_service=position_svc,
            llm_service=llm_svc,
            agents=agents,
        )
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-sel", "answers": {"1": [{"value": 1}]}}
            ),
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.error_response is None
        assert result.prepared_message == "診断完了"
        position_svc.update_jobtypes.assert_awaited_once_with(["エンジニア"])

    @pytest.mark.asyncio
    async def test_initial_menu_calls_create_session(self):
        """B-NEW1: workflow_id == INITIAL_MENU_WORKFLOW_ID → create_session(ChatSessionStatus.CHATTING) が呼ばれる。"""
        from domain.entities.chat_session import ChatSessionStatus
        from utils.const import INITIAL_MENU_WORKFLOW_ID

        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(WorkflowPostProcessingResult(message="開始します。"), [])
        )
        create_session = MagicMock()
        handler = _make_handler(
            workflow_service=workflow_svc,
            create_session=create_session,
        )
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": INITIAL_MENU_WORKFLOW_ID, "answers": {"1": [{"value": 1}]}}
            ),
        )
        await handler.prepare_workflow_submitted(request)
        create_session.assert_called_once_with(ChatSessionStatus.CHATTING)

    @pytest.mark.asyncio
    async def test_initial_menu_create_session_raises_propagates(self):
        """B-NEW1-ERR: INITIAL_MENU で create_session が例外を上げた場合、例外が伝播すること。"""
        from utils.const import INITIAL_MENU_WORKFLOW_ID

        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(WorkflowPostProcessingResult(message="開始します。"), [])
        )
        create_session = MagicMock(side_effect=Exception("DB接続エラー"))
        handler = _make_handler(
            workflow_service=workflow_svc,
            create_session=create_session,
        )
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": INITIAL_MENU_WORKFLOW_ID, "answers": {"1": [{"value": 1}]}}
            ),
        )
        with pytest.raises(Exception, match="DB接続エラー"):
            await handler.prepare_workflow_submitted(request)

    @pytest.mark.asyncio
    async def test_non_initial_menu_does_not_call_create_session(self):
        """B-NEW2: INITIAL_MENU 以外では create_session が呼ばれない。"""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(WorkflowPostProcessingResult(message="ok"), [])
        )
        create_session = MagicMock()
        handler = _make_handler(
            workflow_service=workflow_svc,
            create_session=create_session,
        )
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "other-workflow", "answers": {"1": [{"value": 1}]}}
            ),
        )
        await handler.prepare_workflow_submitted(request)
        create_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_next_agent_name(self):
        """B-NEW3: post_result.next_agent_name が result.next_agent_name に反映される。"""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(message="ok", next_agent_name="CareerAdvisor"),
                [],
            )
        )
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-x", "answers": {"1": [{"value": 1}]}}
            ),
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.next_agent_name == "CareerAdvisor"

    @pytest.mark.asyncio
    async def test_returns_workflow_id(self):
        """B-NEW4: result.workflow_id に処理した workflow_id の値が入る。"""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(WorkflowPostProcessingResult(message="ok"), [])
        )
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "my-workflow", "answers": {"1": [{"value": 1}]}}
            ),
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.workflow_id == "my-workflow"

    @pytest.mark.asyncio
    async def test_returns_next_workflow_id_response(self):
        """B-NEW5: post_result.next_workflow_id がある場合 result.next_workflow_id_response が非 None かつ WORKFLOW 型。"""
        from unittest.mock import MagicMock

        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(message="ok", next_workflow_id="next-wf"),
                [],
            )
        )
        next_def = MagicMock()
        next_def.model_dump.return_value = {"id": "next-wf"}
        workflow_svc.get_definition.return_value = next_def
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-y", "answers": {"1": [{"value": 1}]}}
            ),
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.next_workflow_id_response is not None
        assert result.next_workflow_id_response.response_type == ChatResponseType.WORKFLOW

    @pytest.mark.asyncio
    async def test_next_workflow_id_definition_not_found_returns_error_response(self):
        """B-NEW5b: get_definition が FileNotFoundError → result.next_workflow_id_response がエラーレスポンス。"""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(message="ok", next_workflow_id="missing-wf"),
                [],
            )
        )
        workflow_svc.get_definition.side_effect = FileNotFoundError("not found")
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-z", "answers": {"1": [{"value": 1}]}}
            ),
        )
        result = await handler.prepare_workflow_submitted(request)
        assert result.next_workflow_id_response is not None
        assert result.next_workflow_id_response.response_type == ChatResponseType.ERROR

    @pytest.mark.asyncio
    async def test_next_workflow_id_appends_start_workflow_tool_history(self):
        """next_workflow_id がある場合、start_workflow の tool レコードが履歴末尾に追加される。"""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(message="ok", next_workflow_id="next-wf"),
                [{"role": LLMMessageRole.ASSISTANT, "content": "質問"}],
            )
        )
        next_def = MagicMock()
        next_def.model_dump.return_value = {"id": "next-wf"}
        workflow_svc.get_definition.return_value = next_def
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-y", "answers": {"1": [{"value": 1}]}}
            ),
        )

        result = await handler.prepare_workflow_submitted(request)

        tool_record = result.workflow_histories[-1]
        assert tool_record.role == LLMMessageRole.TOOL
        assert tool_record.tool_name == ToolName.START_WORKFLOW
        assert tool_record.tool_call_id.startswith("wf_chain_")
        assert json.loads(tool_record.content) == {"WorkflowID": "next-wf"}
        assert tool_record.tool_input == {"WorkflowID": "next-wf"}
        # message_id はフロントへ返す WORKFLOW レスポンスと一致する
        assert tool_record.message_id == result.next_workflow_id_response.message_id

    @pytest.mark.asyncio
    async def test_next_workflow_id_definition_error_does_not_append_tool_history(self):
        """定義取得に失敗した場合、start_workflow の tool レコードは追加されない。"""
        workflow_svc = MagicMock()
        workflow_svc.process_workflow_submission = AsyncMock(
            return_value=(
                WorkflowPostProcessingResult(message="ok", next_workflow_id="missing-wf"),
                [],
            )
        )
        workflow_svc.get_definition.side_effect = FileNotFoundError("not found")
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            message=json.dumps(
                {"workflow_id": "wf-z", "answers": {"1": [{"value": 1}]}}
            ),
        )

        result = await handler.prepare_workflow_submitted(request)

        assert result.workflow_histories == []


# ---------------------------------------------------------------------------
# prepare_workflow_cancelled tests
# ---------------------------------------------------------------------------


class TestPrepareWorkflowCancelled:
    @pytest.mark.asyncio
    async def test_json_decode_error_returns_fallback_message(self):
        """B23: Invalid JSON → fallback message without workflow id."""
        handler = _make_handler()
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_CANCELLED, message="{invalid"
        )
        result = await handler.prepare_workflow_cancelled(request)
        assert result.error_response is None
        assert "ワークフロー" in result.prepared_message
        # No backtick-quoted workflow ID in the fallback
        assert "`" not in result.prepared_message

    @pytest.mark.asyncio
    async def test_type_error_returns_fallback_message(self):
        """B24: Non-dict JSON (null) → TypeError → fallback message."""
        handler = _make_handler()
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_CANCELLED, message="null"
        )
        result = await handler.prepare_workflow_cancelled(request)
        assert result.error_response is None
        assert "ワークフロー" in result.prepared_message
        assert "`" not in result.prepared_message

    @pytest.mark.asyncio
    async def test_empty_workflow_id_returns_fallback_message(self):
        """B25: workflow_id is empty string → fallback message."""
        handler = _make_handler()
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_CANCELLED,
            message=json.dumps({}),
        )
        result = await handler.prepare_workflow_cancelled(request)
        assert result.error_response is None
        assert "ワークフロー" in result.prepared_message
        assert "`" not in result.prepared_message

    @pytest.mark.asyncio
    async def test_unknown_workflow_id_returns_fallback_message(self):
        """B26: exists_definition returns False → fallback message."""
        workflow_svc = MagicMock()
        workflow_svc.exists_definition.return_value = False
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_CANCELLED,
            message=json.dumps({"workflow_id": "unknown"}),
        )
        result = await handler.prepare_workflow_cancelled(request)
        assert result.error_response is None
        assert "ワークフロー" in result.prepared_message
        assert "`" not in result.prepared_message
        workflow_svc.exists_definition.assert_called_once_with("unknown")

    @pytest.mark.asyncio
    async def test_known_workflow_id_returns_named_message(self):
        """B27: workflow_id present and exists → message with backtick-quoted id."""
        workflow_svc = MagicMock()
        workflow_svc.exists_definition.return_value = True
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_CANCELLED,
            message=json.dumps({"workflow_id": "career-fit"}),
        )
        result = await handler.prepare_workflow_cancelled(request)
        assert result.error_response is None
        assert "`career-fit`" in result.prepared_message

    @pytest.mark.asyncio
    async def test_initial_menu_cancel_returns_error(self):
        """B-NEW7: workflow_id == INITIAL_MENU_WORKFLOW_ID → result.error_response が非 None。"""
        from utils.const import INITIAL_MENU_WORKFLOW_ID

        handler = _make_handler()
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_CANCELLED,
            message=json.dumps({"workflow_id": INITIAL_MENU_WORKFLOW_ID}),
        )
        result = await handler.prepare_workflow_cancelled(request)
        assert result.error_response is not None
        assert result.error_response.message == "このワークフローはキャンセルできません。"

    @pytest.mark.asyncio
    async def test_non_initial_menu_cancel_is_allowed(self):
        """B-NEW8: INITIAL_MENU 以外の cancel は従来通り error_response is None。"""
        workflow_svc = MagicMock()
        workflow_svc.exists_definition.return_value = True
        handler = _make_handler(workflow_service=workflow_svc)
        request = _make_request(
            request_type=ChatRequestType.WORKFLOW_CANCELLED,
            message=json.dumps({"workflow_id": "other-wf"}),
        )
        result = await handler.prepare_workflow_cancelled(request)
        assert result.error_response is None


# ---------------------------------------------------------------------------
# _update_agents_with_position_search_tool tests
# ---------------------------------------------------------------------------


class TestUpdateAgentsWithPositionSearchTool:
    def test_empty_updated_agents_returns_false(self):
        """B28: update_agent_by_tool_name returns ({}, ...) → return False."""
        llm_svc = MagicMock()
        llm_svc.update_agent_by_tool_name.return_value = ({}, "search_tool")
        handler = _make_handler(llm_service=llm_svc)
        result = handler._update_agents_with_position_search_tool(
            "search_tool", ["エンジニア"]
        )
        assert result is False

    def test_mismatched_tool_name_returns_false(self):
        """B29: tool_name not None, configured != requested → return False."""
        agents = {"CareerAdvisor": (MagicMock(), True)}
        llm_svc = MagicMock()
        llm_svc.update_agent_by_tool_name.return_value = (agents, "other_tool")
        handler = _make_handler(llm_service=llm_svc, agents=agents)
        result = handler._update_agents_with_position_search_tool(
            "search_tool", ["エンジニア"]
        )
        assert result is False

    def test_matching_tool_name_returns_true(self):
        """B30: tool_name not None, configured == requested → return True."""
        agents = {"CareerAdvisor": (MagicMock(), True)}
        llm_svc = MagicMock()
        llm_svc.update_agent_by_tool_name.return_value = (agents, "search_tool")
        handler = _make_handler(llm_service=llm_svc, agents=agents)
        result = handler._update_agents_with_position_search_tool(
            "search_tool", ["エンジニア"]
        )
        assert result is True

    def test_none_tool_name_skips_name_check_and_returns_true(self):
        """B31: tool_name is None → skip tool_name comparison → return True."""
        agents = {"CareerAdvisor": (MagicMock(), True)}
        llm_svc = MagicMock()
        # configured_tool_name could be anything; comparison is skipped when tool_name is None
        llm_svc.update_agent_by_tool_name.return_value = (agents, None)
        handler = _make_handler(llm_service=llm_svc, agents=agents)
        result = handler._update_agents_with_position_search_tool(None, None)
        assert result is True
