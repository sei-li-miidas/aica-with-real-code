"""Unit tests for PositionService residual parity coverage."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from repositories.action_log_repo import ActionLogRepository, ActionLogType
from repositories.api_repo import AICAAPIRepository
from repositories.chat_repo import ChatRepository
from repositories.position_repo import PositionRepository
from repositories.user_repo import UserRepository
from services.position_service import PositionService

pytestmark = pytest.mark.pre_extraction_parity


@pytest.fixture
def deps():
    position_repository = Mock(spec=PositionRepository)
    position_repository.get_company_detail.return_value = None
    position_repository.get_business_detail.return_value = None
    position_repository.get_cached_position_search_result.return_value = None
    position_repository.remove_search_result_positions_ids.return_value = 0
    position_repository.process_and_cache_positions.return_value = []
    position_repository.process_position_search_result.return_value = {"Positions": []}

    return dict(
        position_repository=position_repository,
        aica_api_repository=AsyncMock(spec=AICAAPIRepository),
        chat_repository=Mock(spec=ChatRepository),
        user_repository=Mock(spec=UserRepository),
        action_log_repository=MagicMock(spec=ActionLogRepository),
    )


@pytest.fixture
def svc(deps):
    return PositionService(**deps)


@pytest.mark.asyncio
async def test_get_business_detail_decrypt_error_returns_none(svc):
    with patch("services.position_service.decrypt", side_effect=Exception("bad")):
        result = await svc.get_business_detail("enc-pid", encrypted=True)
    assert result is None


@pytest.mark.asyncio
async def test_get_position_detail_decrypt_error_returns_none(svc):
    with patch("services.position_service.decrypt", side_effect=Exception("bad")):
        result = await svc.get_position_detail("enc-pid", encrypted=True)
    assert result is None


@pytest.mark.asyncio
async def test_get_company_detail_decrypt_error_returns_none(svc):
    with patch("services.position_service.decrypt", side_effect=Exception("bad")):
        result = await svc.get_company_detail("enc-pid", encrypted=True)
    assert result is None


@pytest.mark.asyncio
async def test_get_company_detail_cache_hit(svc, deps):
    deps["position_repository"].get_company_detail.return_value = {"Company": "cached"}
    result = await svc.get_company_detail("pid", encrypted=False)
    assert result == {"Company": "cached"}
    deps["aica_api_repository"].get.assert_not_called()


@pytest.mark.asyncio
async def test_get_company_detail_api_none_returns_none(svc, deps):
    deps["aica_api_repository"].get.return_value = (200, None)
    result = await svc.get_company_detail("pid", encrypted=False)
    assert result is None


@pytest.mark.asyncio
async def test_get_company_detail_api_success_saves_cache(svc, deps):
    deps["aica_api_repository"].get.return_value = (200, {"Company": "api"})
    result = await svc.get_company_detail("pid", encrypted=False)
    assert result == {"Company": "api"}
    deps["position_repository"].save_company_detail.assert_called_once_with(
        "pid",
        {"Company": "api"},
    )


@pytest.mark.asyncio
async def test_get_business_detail_cache_hit(svc, deps):
    deps["position_repository"].get_business_detail.return_value = {
        "Business": "cached"
    }
    result = await svc.get_business_detail("pid", encrypted=False)
    assert result == {"Business": "cached"}
    deps["aica_api_repository"].get.assert_not_called()


@pytest.mark.asyncio
async def test_get_business_detail_api_none(svc, deps):
    deps["aica_api_repository"].get.return_value = (200, None)
    result = await svc.get_business_detail("pid", encrypted=False)
    assert result is None


@pytest.mark.asyncio
async def test_get_position_recommendation_theme_not_decrypted_returns_none(svc):
    with patch("services.position_service.decrypt", return_value=""):
        result = await svc.get_position_recommendation("enc-theme")
    assert result is None


@pytest.mark.asyncio
async def test_get_position_recommendation_missing_positions_returns_none(svc, deps):
    with patch("services.position_service.decrypt", return_value="theme-a"):
        deps["aica_api_repository"].get.return_value = (200, {"foo": "bar"})
        result = await svc.get_position_recommendation("enc-theme")
    assert result is None


@pytest.mark.asyncio
async def test_get_position_recommendation_success_logs_count(svc, deps):
    payload = {
        "Positions": [{"ID": "p1"}],
        "AllPositionIds": ["p1", "p2"],
    }
    deps["position_repository"].process_and_cache_positions.return_value = [
        {"ID": "p1"}
    ]

    with patch("services.position_service.decrypt", return_value="theme-a"):
        deps["aica_api_repository"].get.return_value = (200, payload)
        result = await svc.get_position_recommendation("enc-theme")

    assert result == [{"ID": "p1"}]
    deps["action_log_repository"].insert.assert_called_once_with(
        log_type=ActionLogType.RECOMMENDATION,
        source="theme-a",
        content={"count": 2},
    )


@pytest.mark.asyncio
async def test_search_positions_by_tool_call_id_missing_tool_input_returns_none(
    svc, deps
):
    deps["chat_repository"].get_tool_input.return_value = None
    result = await svc.search_positions_by_tool_call_id("call-x")
    assert result is None


@pytest.mark.asyncio
async def test_search_positions_by_tool_call_id_success_removes_request_keys(svc, deps):
    tool_input = {"RequestID": "r-1", "SessionID": "s-1", "Keyword": "python"}
    deps["chat_repository"].get_tool_input.return_value = tool_input
    deps["aica_api_repository"].post.return_value = (
        200,
        {"Positions": [{"ID": 1}], "AllPositionIds": [1]},
    )
    deps["position_repository"].process_position_search_result.return_value = {
        "Positions": [{"ID": 1}]
    }

    result = await svc.search_positions_by_tool_call_id("call-1")

    assert result == {"Positions": [{"ID": 1}]}
    deps["aica_api_repository"].post.assert_awaited_once_with(
        "positions/search",
        json={"Keyword": "python"},
    )


@pytest.mark.asyncio
async def test_search_positions_by_tool_call_id_missing_positions_returns_none(
    svc, deps
):
    deps["chat_repository"].get_tool_input.return_value = {"Keyword": "x"}
    deps["aica_api_repository"].post.return_value = (200, {"foo": "bar"})
    result = await svc.search_positions_by_tool_call_id("call-1")
    assert result is None


@pytest.mark.asyncio
async def test_jobtype_specific_position_search_none_response_returns_none(svc, deps):
    deps["aica_api_repository"].post.return_value = (200, None)
    result = await svc.jobtype_specific_position_search({"JobtypeNames": ["eng"]})
    assert result is None


@pytest.mark.asyncio
async def test_jobtype_specific_position_search_success(svc, deps):
    deps["aica_api_repository"].post.return_value = (
        200,
        {"Positions": [{"ID": 7}], "AllPositionIds": [7]},
    )
    deps["position_repository"].process_position_search_result.return_value = {
        "Positions": [{"ID": 7}]
    }

    with patch("services.position_service.uuid.uuid4", return_value="fake-uuid"):
        result = await svc.jobtype_specific_position_search({"JobtypeNames": ["eng"]})

    assert result == {"Positions": [{"ID": 7}]}
    deps["position_repository"].process_position_search_result.assert_called_once_with(
        "fake-uuid",
        {"Positions": [{"ID": 7}], "AllPositionIds": [7]},
    )


@pytest.mark.asyncio
async def test_load_more_cache_miss_without_all_position_ids_returns_empty(svc, deps):
    deps["position_repository"].get_cached_position_search_result.return_value = []
    deps["chat_repository"].get_tool_output.return_value = json.dumps(
        {"text": json.dumps({"foo": "bar"})}
    )

    count, positions = await svc.load_more("search-1", offset=0, limit=3)

    assert count == 0
    assert positions == []


@pytest.mark.asyncio
async def test_load_more_cache_miss_without_text_raises_type_error(svc, deps):
    deps["position_repository"].get_cached_position_search_result.return_value = []
    deps["chat_repository"].get_tool_output.return_value = json.dumps({"no_text": "x"})

    with pytest.raises(TypeError):
        await svc.load_more("search-1", offset=0, limit=3)


@pytest.mark.asyncio
async def test_load_more_cache_miss_saves_position_ids(svc, deps):
    deps["position_repository"].get_cached_position_search_result.return_value = []
    deps["chat_repository"].get_tool_output.return_value = json.dumps(
        {"text": json.dumps({"AllPositionIds": [1, 2, 3]})}
    )
    deps["aica_api_repository"].post.return_value = (
        200,
        {"Positions": [{"ID": 1}, {"ID": 2}]},
    )
    deps["position_repository"].process_and_cache_positions.return_value = [
        {"ID": 1},
        {"ID": 2},
    ]

    count, positions = await svc.load_more("search-5", offset=0, limit=2)

    assert count == 2
    assert positions == [{"ID": 1}, {"ID": 2}]
    deps["position_repository"].save_search_result_position_ids.assert_called_once_with(
        "search-5",
        [1, 2, 3],
    )


@pytest.mark.asyncio
async def test_load_more_cache_miss_with_invalid_json_raises(svc, deps):
    deps["position_repository"].get_cached_position_search_result.return_value = []
    deps["chat_repository"].get_tool_output.return_value = json.dumps(
        {"text": "not-json"}
    )

    with pytest.raises(UnboundLocalError):
        await svc.load_more("search-1", offset=0, limit=2)


@pytest.mark.asyncio
async def test_load_more_api_missing_positions_removes_requested_ids(svc, deps):
    deps["position_repository"].get_cached_position_search_result.return_value = [
        1,
        2,
        3,
    ]
    deps["aica_api_repository"].post.return_value = (200, None)
    deps["position_repository"].remove_search_result_positions_ids.return_value = 11

    count, positions = await svc.load_more("search-2", offset=0, limit=2)

    assert count == 11
    assert positions == []
    deps[
        "position_repository"
    ].remove_search_result_positions_ids.assert_called_once_with(
        "search-2",
        [1, 2],
    )


@pytest.mark.asyncio
async def test_load_more_success_with_missing_summaries_removes_only_missing_ids(
    svc, deps
):
    deps["position_repository"].get_cached_position_search_result.return_value = [
        1,
        2,
        3,
    ]
    deps["aica_api_repository"].post.return_value = (
        200,
        {"Positions": [{"ID": 1}]},
    )
    deps["position_repository"].process_and_cache_positions.return_value = [
        {"ID": 1, "Name": "A"}
    ]
    deps["position_repository"].remove_search_result_positions_ids.return_value = 21

    count, positions = await svc.load_more("search-3", offset=0, limit=2)

    assert count == 21
    assert positions == [{"ID": 1, "Name": "A"}]
    deps[
        "position_repository"
    ].remove_search_result_positions_ids.assert_called_once_with(
        "search-3",
        [2],
    )


@pytest.mark.asyncio
async def test_load_more_success_all_summaries_available_returns_slice_length(
    svc, deps
):
    deps["position_repository"].get_cached_position_search_result.return_value = [
        10,
        20,
        30,
    ]
    deps["aica_api_repository"].post.return_value = (
        200,
        {"Positions": [{"ID": 20}, {"ID": 30}]},
    )
    deps["position_repository"].process_and_cache_positions.return_value = [
        {"ID": 20},
        {"ID": 30},
    ]

    count, positions = await svc.load_more("search-4", offset=1, limit=2)

    assert count == 2
    assert positions == [{"ID": 20}, {"ID": 30}]
    deps["position_repository"].remove_search_result_positions_ids.assert_not_called()


@pytest.mark.asyncio
async def test_update_jobtypes_nonstr_tool_name_returns_none(svc, deps):
    deps["aica_api_repository"].post.return_value = (200, {"ToolName": 123})
    result = await svc.update_jobtypes(["eng"])
    assert result is None


@pytest.mark.asyncio
async def test_update_jobtypes_nondict_response_returns_none(svc, deps):
    deps["aica_api_repository"].post.return_value = (200, None)
    result = await svc.update_jobtypes(["eng"])
    assert result is None


@pytest.mark.asyncio
async def test_update_jobtypes_blank_tool_name_returns_none(svc, deps):
    deps["aica_api_repository"].post.return_value = (200, {"ToolName": "   "})
    result = await svc.update_jobtypes(["eng"])
    assert result is None


@pytest.mark.asyncio
async def test_jobtype_other_filter_uses_get(svc, deps):
    deps["aica_api_repository"].get.return_value = (200, {"items": [1]})
    result = await svc.jobtype_other_filter("other")
    assert result == {"items": [1]}


@pytest.mark.asyncio
async def test_current_search_filter_returns_none(svc, deps):
    deps["aica_api_repository"].get.return_value = (200, None)
    result = await svc.current_search_filter()
    assert result is None


@pytest.mark.asyncio
async def test_clear_jobtypes_posts_clear_endpoint(svc, deps):
    deps["aica_api_repository"].post.return_value = (200, None)

    result = await svc.clear_jobtypes()

    assert result is None
    deps["aica_api_repository"].post.assert_awaited_once_with(
        "positions/jobtypes/clear"
    )
