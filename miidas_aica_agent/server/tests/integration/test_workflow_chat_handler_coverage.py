"""
Integration tests for WorkflowChatHandler — targeting 100% branch coverage.

Tests call the real WorkflowChatHandler directly.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from services.chat.workflow_chat_handler import (
    WorkflowChatHandler,
    WorkflowChatHandlerResult,
)
from services.workflow_handlers.base import WorkflowPostProcessingResult
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.enum import PageName

pytestmark = pytest.mark.pre_extraction_parity


def _make_request(message: str = "{}") -> ChatRequestModel:
    return ChatRequestModel(
        request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
        current_page=PageName.CHAT,
        message=message,
        current_message_id="msg-1",
    )


def _make_handler(
    position_service=None,
    workflow_service=None,
    llm_service=None,
) -> WorkflowChatHandler:
    pos_svc = position_service or MagicMock()
    wf_svc = workflow_service or MagicMock()
    llm_svc = llm_service or MagicMock()

    return WorkflowChatHandler(
        position_service=pos_svc,
        workflow_service=wf_svc,
        llm_service=llm_svc,
        create_session=Mock(),
        get_agents=Mock(return_value={}),
        get_provider=Mock(return_value="gpt-4o"),
        get_active_agent_name=Mock(return_value="CareerAdvisor"),
    )


# ─── prepare_workflow_submitted with selected_jobtypes ───────────────────────


@pytest.mark.asyncio
async def test_prepare_workflow_submitted_with_selected_jobtypes_success():
    """Lines 262-267: selected_jobtypes is truthy, _apply_jobtypes succeeds (returns None)."""
    from utils.log_utils import set_session_id, clear_session_id

    wf_svc = MagicMock()
    post_result = WorkflowPostProcessingResult(
        message="Workflow done",
        selected_jobtypes=["営業", "エンジニア"],
    )
    wf_svc.process_workflow_submission = AsyncMock(return_value=(post_result, []))
    wf_svc.exists_definition.return_value = True

    pos_svc = MagicMock()
    pos_svc.update_jobtypes = AsyncMock(return_value="search_tool")
    pos_svc.clear_jobtypes = AsyncMock()

    llm_svc = MagicMock()
    llm_svc.update_agent_by_tool_name.return_value = (
        {"Agent": MagicMock()},
        "search_tool",
    )

    handler = _make_handler(
        position_service=pos_svc,
        workflow_service=wf_svc,
        llm_service=llm_svc,
    )

    # workflow_submitted message with answers
    answers = {"1": [{"value": 1}]}
    import json

    request = ChatRequestModel(
        request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
        current_page=PageName.CHAT,
        message=json.dumps({"workflow_id": "some_workflow", "answers": answers}),
        current_message_id="msg-wf",
    )

    set_session_id("sess-wf")
    try:
        result = await handler.prepare_workflow_submitted(request)
    finally:
        clear_session_id()

    assert isinstance(result, WorkflowChatHandlerResult)
    assert result.error_response is None
    assert result.prepared_message == "Workflow done"


@pytest.mark.asyncio
async def test_prepare_workflow_submitted_selected_jobtypes_apply_fails():
    """Lines 266-267: selected_jobtypes truthy, _apply_jobtypes_and_update_agents returns error."""
    from utils.log_utils import set_session_id, clear_session_id

    wf_svc = MagicMock()
    post_result = WorkflowPostProcessingResult(
        message="Workflow done",
        selected_jobtypes=["営業"],
    )
    wf_svc.process_workflow_submission = AsyncMock(return_value=(post_result, []))
    wf_svc.exists_definition.return_value = True

    pos_svc = MagicMock()
    # update_jobtypes returns None → tool_name is None → triggers error path
    pos_svc.update_jobtypes = AsyncMock(return_value=None)

    llm_svc = MagicMock()
    llm_svc.update_agent_by_tool_name.return_value = (None, None)

    handler = _make_handler(
        position_service=pos_svc,
        workflow_service=wf_svc,
        llm_service=llm_svc,
    )

    answers = {"1": [{"value": 1}]}
    import json

    request = ChatRequestModel(
        request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
        current_page=PageName.CHAT,
        message=json.dumps({"workflow_id": "some_workflow", "answers": answers}),
        current_message_id="msg-wf-fail",
    )

    set_session_id("sess-wf-fail")
    try:
        result = await handler.prepare_workflow_submitted(request)
    finally:
        clear_session_id()

    assert isinstance(result, WorkflowChatHandlerResult)
