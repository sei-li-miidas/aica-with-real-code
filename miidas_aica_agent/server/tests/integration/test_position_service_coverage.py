"""
Integration tests for PositionService — targeting 100% branch coverage.

Tests call the real service with mocked repositories and mocked API.
"""

import json
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from repositories.action_log_repo import ActionLogRepository
from repositories.api_repo import AICAAPIRepository
from repositories.chat_repo import ChatRepository
from repositories.position_repo import PositionRepository
from repositories.user_repo import UserRepository
from services.position_service import PositionService

pytestmark = pytest.mark.pre_extraction_parity


def _make_svc(**overrides) -> PositionService:
    defaults = dict(
        position_repository=Mock(spec=PositionRepository),
        aica_api_repository=MagicMock(spec=AICAAPIRepository),
        chat_repository=Mock(spec=ChatRepository),
        user_repository=Mock(spec=UserRepository),
        action_log_repository=MagicMock(),
    )
    defaults.update(overrides)
    svc = PositionService(**defaults)
    # Make all async methods async by default
    svc._aica_api_repository.post = AsyncMock(return_value=(200, None))
    svc._aica_api_repository.get = AsyncMock(return_value=(200, None))
    return svc


# ─── get_position_detail ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_position_detail_encrypted_invalid_raises_and_returns_none():
    svc = _make_svc()
    # An invalid encrypted value should cause decrypt to raise
    result = await svc.get_position_detail("invalid-encrypted-id", encrypted=True)
    assert result is None


@pytest.mark.asyncio
async def test_get_position_detail_unencrypted_cache_hit():
    svc = _make_svc()
    cached = {"Position": {"ID": 42}}
    svc._position_repository.get_position_detail.return_value = cached
    svc._user_repository.get_applied_position_ids.return_value = []

    result = await svc.get_position_detail("42", encrypted=False)
    assert result == {**cached, "Applied": False}
    # Should not call API when cache hits
    svc._aica_api_repository.post.assert_not_called()


@pytest.mark.asyncio
async def test_get_position_detail_unencrypted_cache_miss_calls_api():
    svc = _make_svc()
    svc._position_repository.get_position_detail.return_value = None
    api_result = {"Position": {"ID": 99}}
    svc._aica_api_repository.post = AsyncMock(return_value=(200, api_result))
    svc._user_repository.get_applied_position_ids.return_value = ["99"]

    result = await svc.get_position_detail("99", encrypted=False)

    assert result is not None
    assert result["Applied"] is True
    svc._position_repository.save_position_detail.assert_called_once()


@pytest.mark.asyncio
async def test_get_position_detail_api_returns_none():
    svc = _make_svc()
    svc._position_repository.get_position_detail.return_value = None
    svc._aica_api_repository.post = AsyncMock(return_value=(404, None))

    result = await svc.get_position_detail("100", encrypted=False)
    assert result is None
    svc._position_repository.save_position_detail.assert_not_called()


@pytest.mark.asyncio
async def test_get_position_detail_applied_position_ids_none():
    svc = _make_svc()
    svc._position_repository.get_position_detail.return_value = None
    svc._aica_api_repository.post = AsyncMock(return_value=(200, {"Position": {}}))
    svc._user_repository.get_applied_position_ids.return_value = None

    result = await svc.get_position_detail("5", encrypted=False)
    assert result is not None
    assert result["Applied"] is False


# ─── get_company_detail ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_company_detail_encrypted_invalid_returns_none():
    svc = _make_svc()
    result = await svc.get_company_detail("bad-encrypted", encrypted=True)
    assert result is None


@pytest.mark.asyncio
async def test_get_company_detail_cache_hit():
    svc = _make_svc()
    cached = {"Company": {"Name": "テスト株式会社"}}
    svc._position_repository.get_company_detail.return_value = cached

    result = await svc.get_company_detail("42", encrypted=False)
    assert result == cached
    svc._aica_api_repository.get.assert_not_called()


@pytest.mark.asyncio
async def test_get_company_detail_cache_miss_calls_api_and_saves():
    svc = _make_svc()
    svc._position_repository.get_company_detail.return_value = None
    company = {"Company": {"Name": "株式会社ABC"}}
    svc._aica_api_repository.get = AsyncMock(return_value=(200, company))

    result = await svc.get_company_detail("42", encrypted=False)
    assert result == company
    svc._position_repository.save_company_detail.assert_called_once()


@pytest.mark.asyncio
async def test_get_company_detail_api_returns_none():
    svc = _make_svc()
    svc._position_repository.get_company_detail.return_value = None
    svc._aica_api_repository.get = AsyncMock(return_value=(404, None))

    result = await svc.get_company_detail("42", encrypted=False)
    assert result is None
    svc._position_repository.save_company_detail.assert_not_called()


# ─── get_business_detail ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_business_detail_encrypted_invalid_returns_none():
    svc = _make_svc()
    result = await svc.get_business_detail("bad-enc", encrypted=True)
    assert result is None


@pytest.mark.asyncio
async def test_get_business_detail_cache_hit():
    svc = _make_svc()
    cached = {"Business": {"Name": "IT"}}
    svc._position_repository.get_business_detail.return_value = cached

    result = await svc.get_business_detail("42", encrypted=False)
    assert result == cached
    svc._aica_api_repository.get.assert_not_called()


@pytest.mark.asyncio
async def test_get_business_detail_cache_miss_calls_api():
    svc = _make_svc()
    svc._position_repository.get_business_detail.return_value = None
    business = {"Business": {"Name": "金融"}}
    svc._aica_api_repository.get = AsyncMock(return_value=(200, business))

    result = await svc.get_business_detail("42", encrypted=False)
    assert result == business
    svc._position_repository.save_business_detail.assert_called_once()


@pytest.mark.asyncio
async def test_get_business_detail_api_returns_none():
    svc = _make_svc()
    svc._position_repository.get_business_detail.return_value = None
    svc._aica_api_repository.get = AsyncMock(return_value=(404, None))

    result = await svc.get_business_detail("42", encrypted=False)
    assert result is None


# ─── get_position_recommendation ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_position_recommendation_empty_theme_returns_none():
    svc = _make_svc()
    # decrypt of an empty string → empty string → falsy → returns None
    # Patch decrypt to return ""
    from unittest.mock import patch

    with patch("services.position_service.decrypt", return_value=""):
        result = await svc.get_position_recommendation("encrypted-theme")
    assert result is None


@pytest.mark.asyncio
async def test_get_position_recommendation_api_returns_no_positions():
    svc = _make_svc()
    from unittest.mock import patch

    with patch("services.position_service.decrypt", return_value="some-theme"):
        svc._aica_api_repository.get = AsyncMock(return_value=(200, {"other": "data"}))
        result = await svc.get_position_recommendation("encrypted-theme")
    assert result is None


@pytest.mark.asyncio
async def test_get_position_recommendation_api_returns_none():
    svc = _make_svc()
    from unittest.mock import patch

    with patch("services.position_service.decrypt", return_value="some-theme"):
        svc._aica_api_repository.get = AsyncMock(return_value=(404, None))
        result = await svc.get_position_recommendation("encrypted-theme")
    assert result is None


@pytest.mark.asyncio
async def test_get_position_recommendation_success():
    svc = _make_svc()
    positions = [{"ID": 1}, {"ID": 2}]
    svc._position_repository.process_and_cache_positions.return_value = positions
    from unittest.mock import patch

    with patch("services.position_service.decrypt", return_value="theme-1"):
        svc._aica_api_repository.get = AsyncMock(
            return_value=(
                200,
                {"Positions": positions, "AllPositionIds": [1, 2]},
            )
        )
        result = await svc.get_position_recommendation("enc-theme")

    assert result == positions
    svc._action_log_repository.insert.assert_called_once()


# ─── search_positions_by_tool_call_id ────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_positions_by_tool_call_id_no_input_returns_none():
    svc = _make_svc()
    svc._chat_repository.get_tool_input.return_value = None

    result = await svc.search_positions_by_tool_call_id("tool-call-1")
    assert result is None


@pytest.mark.asyncio
async def test_search_positions_by_tool_call_id_api_returns_no_positions():
    svc = _make_svc()
    svc._chat_repository.get_tool_input.return_value = {"JobtypeNames": ["営業"]}
    svc._aica_api_repository.post = AsyncMock(return_value=(200, {}))

    result = await svc.search_positions_by_tool_call_id("tool-call-2")
    assert result is None


@pytest.mark.asyncio
async def test_search_positions_by_tool_call_id_success():
    svc = _make_svc()
    svc._chat_repository.get_tool_input.return_value = {
        "JobtypeNames": ["営業"],
        "RequestID": "r1",
        "SessionID": "s1",
    }
    response = {"Positions": [{"ID": 1}], "AllPositionIds": [1]}
    svc._aica_api_repository.post = AsyncMock(return_value=(200, response))
    svc._position_repository.process_position_search_result.return_value = {
        "result": "ok"
    }

    result = await svc.search_positions_by_tool_call_id("tool-call-3")
    assert result == {"result": "ok"}
    svc._action_log_repository.insert.assert_called_once()


# ─── jobtype_specific_position_search ────────────────────────────────────────


@pytest.mark.asyncio
async def test_jobtype_specific_no_positions_returns_none():
    svc = _make_svc()
    svc._aica_api_repository.post = AsyncMock(return_value=(200, None))
    result = await svc.jobtype_specific_position_search({"filter": "value"})
    assert result is None


@pytest.mark.asyncio
async def test_jobtype_specific_success():
    svc = _make_svc()
    response = {"Positions": [{"ID": 99}], "AllPositionIds": [99]}
    svc._aica_api_repository.post = AsyncMock(return_value=(200, response))
    svc._position_repository.process_position_search_result.return_value = {"ok": True}

    result = await svc.jobtype_specific_position_search({"filter": "v"})
    assert result == {"ok": True}


# ─── load_more ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_more_cache_hit_api_returns_positions():
    svc = _make_svc()
    svc._position_repository.get_cached_position_search_result.return_value = [1, 2, 3]
    positions = [{"ID": 1}, {"ID": 2}]
    svc._aica_api_repository.post = AsyncMock(
        return_value=(200, {"Positions": positions})
    )
    svc._position_repository.process_and_cache_positions.return_value = positions
    svc._position_repository.remove_search_result_positions_ids.return_value = 2

    count, result = await svc.load_more("key-1", 0, 2)
    assert result == positions


@pytest.mark.asyncio
async def test_load_more_cache_miss_reads_from_tool_output():
    svc = _make_svc()
    svc._position_repository.get_cached_position_search_result.return_value = None
    # The service does json.loads(tool_output_str) then .get("text") on the result
    position_search_result = json.dumps({"AllPositionIds": [10, 20]})
    tool_output = json.dumps({"text": position_search_result})
    svc._chat_repository.get_tool_output.return_value = tool_output
    positions = [{"ID": 10}, {"ID": 20}]
    svc._aica_api_repository.post = AsyncMock(
        return_value=(200, {"Positions": positions})
    )
    svc._position_repository.process_and_cache_positions.return_value = positions

    count, result = await svc.load_more("key-2", 0, 3)
    assert result == positions
    svc._position_repository.save_search_result_position_ids.assert_called_once()


@pytest.mark.asyncio
async def test_load_more_cache_miss_no_all_position_ids_returns_zero():
    svc = _make_svc()
    svc._position_repository.get_cached_position_search_result.return_value = None
    # Tool output with no AllPositionIds
    position_search_result = json.dumps({"OtherKey": []})
    tool_output = json.dumps({"text": position_search_result})
    svc._chat_repository.get_tool_output.return_value = tool_output

    count, result = await svc.load_more("key-3", 0, 3)
    assert count == 0
    assert result == []


@pytest.mark.asyncio
async def test_load_more_cache_miss_no_text_key_logs_error():
    """Tests line 319: logs error when position_search_result_str is None/empty.
    Then json.loads(None) raises TypeError → unhandled → propagates."""
    svc = _make_svc()
    svc._position_repository.get_cached_position_search_result.return_value = None
    # Tool output with no 'text' key
    tool_output = json.dumps({"other_key": "value"})
    svc._chat_repository.get_tool_output.return_value = tool_output

    # json.loads(None) raises TypeError since position_search_result_str is None
    with pytest.raises((TypeError, AttributeError)):
        await svc.load_more("key-no-text", 0, 3)


@pytest.mark.asyncio
async def test_load_more_cache_miss_invalid_json_text_logs_exception():
    """Tests lines 326-327: logs exception when text is not valid JSON."""
    svc = _make_svc()
    svc._position_repository.get_cached_position_search_result.return_value = None
    # Tool output where 'text' is invalid JSON
    tool_output = json.dumps({"text": "{invalid json"})
    svc._chat_repository.get_tool_output.return_value = tool_output

    # json.JSONDecodeError caught, then position_search_result_json is unbound
    # which causes UnboundLocalError or NameError
    with pytest.raises(Exception):
        await svc.load_more("key-invalid-json", 0, 3)


@pytest.mark.asyncio
async def test_load_more_api_returns_no_positions():
    svc = _make_svc()
    svc._position_repository.get_cached_position_search_result.return_value = [1, 2]
    svc._aica_api_repository.post = AsyncMock(return_value=(200, None))
    svc._position_repository.remove_search_result_positions_ids.return_value = 0

    count, result = await svc.load_more("key-4", 0, 2)
    assert result == []
    svc._position_repository.remove_search_result_positions_ids.assert_called_once()


@pytest.mark.asyncio
async def test_load_more_some_positions_missing_from_api_response():
    svc = _make_svc()
    svc._position_repository.get_cached_position_search_result.return_value = [1, 2, 3]
    # API only returns position 1 and 2; position 3 is missing
    positions = [{"ID": 1}, {"ID": 2}]
    svc._aica_api_repository.post = AsyncMock(
        return_value=(200, {"Positions": positions})
    )
    svc._position_repository.process_and_cache_positions.return_value = positions
    svc._position_repository.remove_search_result_positions_ids.return_value = 2

    count, result = await svc.load_more("key-5", 0, 3)
    # remove_search_result_positions_ids should be called with the missing id [3]
    call_args = svc._position_repository.remove_search_result_positions_ids.call_args
    assert 3 in call_args[0][1]


@pytest.mark.asyncio
async def test_load_more_all_positions_available_no_remove_call():
    svc = _make_svc()
    svc._position_repository.get_cached_position_search_result.return_value = [1, 2]
    positions = [{"ID": 1}, {"ID": 2}]
    svc._aica_api_repository.post = AsyncMock(
        return_value=(200, {"Positions": positions})
    )
    svc._position_repository.process_and_cache_positions.return_value = positions

    count, result = await svc.load_more("key-6", 0, 2)
    # All positions returned → no non_available_position_ids → count = len(position_ids)
    assert count == 2
    svc._position_repository.remove_search_result_positions_ids.assert_not_called()


# ─── update_jobtypes ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_jobtypes_api_returns_non_dict():
    svc = _make_svc()
    svc._aica_api_repository.post = AsyncMock(return_value=(200, None))
    result = await svc.update_jobtypes(["営業"])
    assert result is None


@pytest.mark.asyncio
async def test_update_jobtypes_no_tool_name_key():
    svc = _make_svc()
    svc._aica_api_repository.post = AsyncMock(return_value=(200, {"other": "key"}))
    result = await svc.update_jobtypes(["営業"])
    assert result is None


@pytest.mark.asyncio
async def test_update_jobtypes_tool_name_not_string():
    svc = _make_svc()
    svc._aica_api_repository.post = AsyncMock(return_value=(200, {"ToolName": 123}))
    result = await svc.update_jobtypes(["営業"])
    assert result is None


@pytest.mark.asyncio
async def test_update_jobtypes_empty_tool_name():
    svc = _make_svc()
    svc._aica_api_repository.post = AsyncMock(return_value=(200, {"ToolName": "   "}))
    result = await svc.update_jobtypes(["営業"])
    assert result is None


@pytest.mark.asyncio
async def test_update_jobtypes_success():
    svc = _make_svc()
    svc._aica_api_repository.post = AsyncMock(
        return_value=(200, {"ToolName": "search_positions"})
    )
    result = await svc.update_jobtypes(["営業"])
    assert result == "search_positions"


# ─── clear_jobtypes ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clear_jobtypes_calls_api():
    svc = _make_svc()
    svc._aica_api_repository.post = AsyncMock(return_value=(200, None))
    await svc.clear_jobtypes()
    svc._aica_api_repository.post.assert_called_once()


# ─── jobtype_other_filter ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_jobtype_other_filter_returns_api_result():
    svc = _make_svc()
    filter_data = {"filters": ["a", "b"]}
    svc._aica_api_repository.get = AsyncMock(return_value=(200, filter_data))
    result = await svc.jobtype_other_filter("営業")
    assert result == filter_data


# ─── current_search_filter ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_current_search_filter_returns_api_result():
    svc = _make_svc()
    filter_data = {"current": "filter"}
    svc._aica_api_repository.get = AsyncMock(return_value=(200, filter_data))
    result = await svc.current_search_filter()
    assert result == filter_data
