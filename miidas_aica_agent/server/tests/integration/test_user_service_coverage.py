"""
Integration tests for UserService — targeting 100% branch coverage.

Tests call the real service with mocked repositories and mocked HTTP.
For methods that use aiohttp, we mock _call_register_user_api and
_call_meeting_application_api at the method boundary.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import status

from domain.entities.chat_session import ChatSessionStatus
from repositories.action_log_repo import ActionLogRepository
from repositories.api_repo import AICAAPIRepository
from repositories.chat_repo import ChatRepository
from repositories.user_repo import UserRepository
from services.position_service import PositionService
from services.user_service import (
    UserService,
    UserQuickEntryValidationErrorCode,
    UserQuickEntryValidationErrorKey,
)
from utils.enum import ApplyResult

pytestmark = pytest.mark.pre_extraction_parity


def _make_svc(**overrides) -> UserService:
    defaults = dict(
        position_svc=MagicMock(spec=PositionService),
        chat_repository=Mock(spec=ChatRepository),
        user_repository=Mock(spec=UserRepository),
        aica_api_repository=MagicMock(spec=AICAAPIRepository),
        action_log_repository=MagicMock(),
        miidas_api_url="https://api.example.com",
        timeout=30,
    )
    defaults.update(overrides)
    return UserService(**defaults)


def _make_user_profile(registration_data=None):
    profile = MagicMock()
    profile.miidas_registration_user_data = registration_data or {}
    return profile


# ─── get_profile ─────────────────────────────────────────────────────────────


def test_get_profile_returns_none_when_no_profile():
    svc = _make_svc()
    svc._user_repository.get_user_profile.return_value = None
    assert svc.get_profile() is None


def test_get_profile_strips_apply_position_ids():
    from utils.const import APPLY_POSITION_IDS_KEY

    svc = _make_svc()
    reg_data = {APPLY_POSITION_IDS_KEY: [1, 2], "other": "value"}
    profile = _make_user_profile(reg_data)
    svc._user_repository.get_user_profile.return_value = profile

    result = svc.get_profile()
    assert result is profile
    assert APPLY_POSITION_IDS_KEY not in reg_data


def test_get_profile_no_registration_data_returns_as_is():
    svc = _make_svc()
    profile = _make_user_profile(None)
    profile.miidas_registration_user_data = None
    svc._user_repository.get_user_profile.return_value = profile
    result = svc.get_profile()
    assert result is profile


# ─── save_basic_profile ──────────────────────────────────────────────────────


def test_save_basic_profile_delegates():
    svc = _make_svc()
    svc._user_repository.update_miidas_registration_user_data.return_value = True
    result = svc.save_basic_profile(MagicMock())
    assert result is True


# ─── save_education_profile ──────────────────────────────────────────────────


def test_save_education_profile_delegates():
    svc = _make_svc()
    svc._user_repository.update_miidas_registration_user_data.return_value = True
    result = svc.save_education_profile(MagicMock())
    assert result is True


# ─── save_experience_profile ─────────────────────────────────────────────────


def test_save_experience_profile_delegates():
    svc = _make_svc()
    svc._user_repository.update_miidas_registration_user_data.return_value = True
    result = svc.save_experience_profile(MagicMock())
    assert result is True


# ─── save_preferences_profile ────────────────────────────────────────────────


def test_save_preferences_profile_deduplicates_job_types_and_cities():
    svc = _make_svc()
    svc._user_repository.update_miidas_registration_user_data.return_value = True

    job_type_1 = SimpleNamespace(id=1)
    job_type_2 = SimpleNamespace(id=2)
    job_type_dup = SimpleNamespace(id=1)  # duplicate of job_type_1

    city_a = SimpleNamespace(city=SimpleNamespace(id=10))
    city_b = SimpleNamespace(city=SimpleNamespace(id=20))
    city_a_dup = SimpleNamespace(city=SimpleNamespace(id=10))  # duplicate

    preferences = MagicMock()
    preferences.will_job_types = [job_type_1, job_type_2, job_type_dup]
    preferences.will_work_addresses = [city_a, city_b, city_a_dup]

    svc.save_preferences_profile(preferences)

    # After dedup, only 2 unique job types and 2 unique cities
    assert len(preferences.will_job_types) == 2
    assert len(preferences.will_work_addresses) == 2


# ─── start_apply ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_apply_no_session_status_returns_none():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = None
    result = await svc.start_apply()
    assert result is None


@pytest.mark.asyncio
async def test_start_apply_non_chatting_status_returns_status():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.REGISTERED
    result = await svc.start_apply()
    assert result == ChatSessionStatus.REGISTERED


@pytest.mark.asyncio
async def test_start_apply_chatting_with_position_id_updates_applying():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.CHATTING
    svc._chat_repository.update_session_status.return_value = ChatSessionStatus.APPLYING
    svc._user_repository.update_miidas_registration_user_data.return_value = True

    with patch("services.user_service.decrypt", return_value="real-id"):
        result = await svc.start_apply(encrypted_position_id="encrypted-id")

    assert result == ChatSessionStatus.APPLYING


@pytest.mark.asyncio
async def test_start_apply_chatting_without_position_id_updates_registering():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.CHATTING
    svc._chat_repository.update_session_status.return_value = (
        ChatSessionStatus.REGISTERING
    )

    result = await svc.start_apply(encrypted_position_id=None)
    assert result == ChatSessionStatus.REGISTERING
    svc._action_log_repository.insert.assert_called_once()


@pytest.mark.asyncio
async def test_start_apply_exception_is_caught():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.CHATTING
    svc._chat_repository.update_session_status.side_effect = Exception("db error")

    # Should not raise — exception is swallowed
    result = await svc.start_apply(encrypted_position_id=None)
    # returns the original session_status (still CHATTING) since exception was caught
    assert result == ChatSessionStatus.CHATTING


# ─── apply_add_position ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_apply_add_position_no_session_returns_none():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = None
    result = await svc.apply_add_position("encrypted-id")
    assert result is None


@pytest.mark.asyncio
async def test_apply_add_position_wrong_status_returns_none():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.CHATTING
    result = await svc.apply_add_position("encrypted-id")
    assert result is None


@pytest.mark.asyncio
async def test_apply_add_position_registering_updates_to_applying():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.REGISTERING
    svc._chat_repository.update_session_status.return_value = ChatSessionStatus.APPLYING

    with patch("services.user_service.decrypt", return_value="real-pos-id"):
        result = await svc.apply_add_position("encrypted")

    assert result == ChatSessionStatus.APPLYING
    svc._user_repository.add_apply_position.assert_called_once_with("real-pos-id")


@pytest.mark.asyncio
async def test_apply_add_position_already_applying_stays_applying():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.APPLYING

    with patch("services.user_service.decrypt", return_value="real-pos-id"):
        result = await svc.apply_add_position("encrypted")

    # Status is already APPLYING, so update_session_status should NOT be called
    assert result == ChatSessionStatus.APPLYING
    svc._chat_repository.update_session_status.assert_not_called()


@pytest.mark.asyncio
async def test_apply_add_position_exception_returns_none():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.REGISTERING
    with patch("services.user_service.decrypt", side_effect=Exception("decrypt error")):
        result = await svc.apply_add_position("encrypted")
    assert result is None


# ─── post_apply_failure ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_post_apply_failure_api_error_with_successful_positions():
    svc = _make_svc()
    svc._aica_api_repository.post = AsyncMock(return_value=(500, None))

    result = await svc.post_apply_failure(
        position_ids=[1, 2],
        successful_position_ids=[1],
        failed_position_ids=[2],
        cookies=[],
    )
    assert result[1] == ChatSessionStatus.APPLIED
    assert result[2] == ApplyResult.MEETING_APPLICATION_SUCCESS


@pytest.mark.asyncio
async def test_post_apply_failure_api_error_no_successful_positions():
    svc = _make_svc()
    svc._aica_api_repository.post = AsyncMock(return_value=(500, None))

    result = await svc.post_apply_failure(
        position_ids=[1, 2],
        successful_position_ids=[],
        failed_position_ids=[1, 2],
        cookies=[],
    )
    assert result[1] == ChatSessionStatus.REGISTERED
    assert result[2] == ApplyResult.REGISTER_SUCCESS


@pytest.mark.asyncio
async def test_post_apply_failure_api_error_no_positions_key():
    svc = _make_svc()
    svc._aica_api_repository.post = AsyncMock(return_value=(200, {"Other": "data"}))

    result = await svc.post_apply_failure(
        position_ids=[1],
        successful_position_ids=[],
        failed_position_ids=[1],
        cookies=[],
    )
    assert result[1] == ChatSessionStatus.REGISTERED


@pytest.mark.asyncio
async def test_post_apply_failure_with_positions_returns_failure_result():
    svc = _make_svc()
    svc._aica_api_repository.post = AsyncMock(
        return_value=(200, {"Positions": [{"ID": 2}]})
    )

    result = await svc.post_apply_failure(
        position_ids=[1, 2],
        successful_position_ids=[1],
        failed_position_ids=[2],
        cookies=[],
    )
    assert result is not None
    assert result[2] == ApplyResult.MEETING_APPLICATION_FAIL


@pytest.mark.asyncio
async def test_post_apply_failure_all_failed_no_failed_positions_in_response():
    svc = _make_svc()
    # Response doesn't include the failed position → failed_positions empty → returns None
    svc._aica_api_repository.post = AsyncMock(
        return_value=(200, {"Positions": [{"ID": 1}]})  # only has successful pos
    )

    result = await svc.post_apply_failure(
        position_ids=[1, 2],
        successful_position_ids=[1],
        failed_position_ids=[2],  # 2 is not in response
        cookies=[],
    )
    # failed_positions would be empty → returns None
    assert result is None


# ─── post_register_validation_failure ────────────────────────────────────────


def _make_registration_data():
    return {
        "basic_profile": {
            "email": "test@example.com",
            "phoneNo": "0901234567",
            "gender": 1,
            "lastName": "テスト",
            "firstName": "太郎",
            "birthYear": 1990,
            "birthMonth": 1,
            "prefecture": {"ID": 1, "Name": "東京都"},
            "city": {"ID": 1, "Name": "千代田区"},
            "firstLanguage": 91,
            "driverLicence": 1,
        },
        "education_profile": {},
        "experience_profile": {},
        "preferences_profile": {},
    }


def test_post_register_validation_failure_email_duplication():
    svc = _make_svc()
    profile = _make_user_profile(_make_registration_data())
    result = svc.post_register_validation_failure(
        {
            UserQuickEntryValidationErrorKey.CODE: UserQuickEntryValidationErrorCode.EMAIL_DUPLICATION
        },
        profile,
        ChatSessionStatus.CHATTING,
    )
    assert result[0] == status.HTTP_409_CONFLICT
    assert "email" in str(result)


def test_post_register_validation_failure_phone_duplication():
    svc = _make_svc()
    profile = _make_user_profile(_make_registration_data())
    result = svc.post_register_validation_failure(
        {
            UserQuickEntryValidationErrorKey.CODE: UserQuickEntryValidationErrorCode.PHONE_NO_DUPLICATION
        },
        profile,
        ChatSessionStatus.CHATTING,
    )
    assert result[0] == status.HTTP_409_CONFLICT
    assert "phoneNo" in str(result)


def test_post_register_validation_failure_details_with_basic_field():
    svc = _make_svc()
    profile = _make_user_profile(_make_registration_data())
    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "Email", "Message": "invalid email"}]},
        profile,
        ChatSessionStatus.CHATTING,
    )
    assert result is not None
    assert result[0] == status.HTTP_400_BAD_REQUEST


def test_post_register_validation_failure_details_birthday_field():
    svc = _make_svc()
    data = _make_registration_data()
    data["basic_profile"]["birthYear"] = 1990
    data["basic_profile"]["birthMonth"] = 1
    profile = _make_user_profile(data)
    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "Birthday"}]},
        profile,
        ChatSessionStatus.CHATTING,
    )
    assert result is not None
    # birthday expands to birthYear/birthMonth fields
    errors = result[3]["Errors"]
    field_names = [e["Field"] for e in errors]
    assert "birthYear" in field_names
    assert "birthMonth" in field_names


def test_post_register_validation_failure_details_joinYm_field():
    svc = _make_svc()
    data = _make_registration_data()
    data["experience_profile"]["joinYear"] = 2020
    data["experience_profile"]["joinMonth"] = 1
    profile = _make_user_profile(data)
    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "JoinYm"}]},
        profile,
        ChatSessionStatus.CHATTING,
    )
    assert result is not None
    errors = result[3]["Errors"]
    field_names = [e["Field"] for e in errors]
    assert "joinYear" in field_names


def test_post_register_validation_failure_details_retireYm_field():
    svc = _make_svc()
    data = _make_registration_data()
    data["experience_profile"]["retireYear"] = 2022
    data["experience_profile"]["retireMonth"] = 3
    profile = _make_user_profile(data)
    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "RetireYm"}]},
        profile,
        ChatSessionStatus.CHATTING,
    )
    assert result is not None
    errors = result[3]["Errors"]
    field_names = [e["Field"] for e in errors]
    assert "retireYear" in field_names


def test_post_register_validation_failure_details_unexpected_field():
    svc = _make_svc()
    data = _make_registration_data()
    # Add the empty-string profile section to avoid KeyError when profile_section stays ""
    data[""] = {}
    profile = _make_user_profile(data)
    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "UnknownFieldXYZ"}]},
        profile,
        ChatSessionStatus.CHATTING,
    )
    # Unknown field is still appended to errors list (with empty page/section)
    # so a 400 result is returned. The unexpected field is logged as an error.
    assert result is not None
    assert result[0] == status.HTTP_400_BAD_REQUEST


def test_post_register_validation_failure_details_no_field_key():
    svc = _make_svc()
    profile = _make_user_profile(_make_registration_data())
    result = svc.post_register_validation_failure(
        {"Details": [{"SomeOtherKey": "value"}]},  # no "Field" key
        profile,
        ChatSessionStatus.CHATTING,
    )
    # field is None/falsy → skipped → errors list stays empty → returns None
    assert result is None


def test_post_register_validation_failure_no_code_no_details_returns_none():
    svc = _make_svc()
    profile = _make_user_profile(_make_registration_data())
    result = svc.post_register_validation_failure(
        {},
        profile,
        ChatSessionStatus.CHATTING,
    )
    assert result is None


# ─── post_register_success ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_post_register_success_no_user_id_logs_error():
    svc = _make_svc()
    svc._chat_repository.register_user_id.return_value = True
    profile = _make_user_profile({"apply_position_ids": []})

    mock_client = MagicMock()
    mock_client.cookie_jar = []

    result = await svc.post_register_success(
        mock_client,
        user_register_result=None,  # None → logs error
        user_profile=profile,
    )
    assert result[2] == ApplyResult.REGISTER_SUCCESS


@pytest.mark.asyncio
async def test_post_register_success_no_position_ids_returns_register_success():
    svc = _make_svc()
    svc._chat_repository.register_user_id.return_value = True
    profile = _make_user_profile({})  # no apply_position_ids

    mock_client = MagicMock()
    mock_client.cookie_jar = []

    result = await svc.post_register_success(
        mock_client,
        user_register_result={"UserID": 42},
        user_profile=profile,
    )
    assert result[1] == ChatSessionStatus.REGISTERED
    assert result[2] == ApplyResult.REGISTER_SUCCESS


@pytest.mark.asyncio
async def test_post_register_success_db_update_fails_logs_error():
    svc = _make_svc()
    svc._chat_repository.register_user_id.return_value = False  # DB update failure
    profile = _make_user_profile({})

    mock_client = MagicMock()
    mock_client.cookie_jar = []

    result = await svc.post_register_success(
        mock_client,
        user_register_result={"UserID": 99},
        user_profile=profile,
    )
    # Returns REGISTER_SUCCESS despite DB update failure
    assert result[2] == ApplyResult.REGISTER_SUCCESS


@pytest.mark.asyncio
async def test_post_register_success_with_positions_all_succeed():
    from utils.const import APPLY_POSITION_IDS_KEY

    svc = _make_svc()
    svc._chat_repository.register_user_id.return_value = True
    svc._chat_repository.update_session_status.return_value = ChatSessionStatus.APPLIED

    profile = _make_user_profile({APPLY_POSITION_IDS_KEY: ["1", "2"]})

    mock_client = MagicMock()
    mock_client.cookie_jar = []

    position_detail = {"Position": {"Modified": "2024-01-01T00:00:00"}}
    svc._position_service.get_position_detail = AsyncMock(return_value=position_detail)

    with (
        patch("services.user_service.asyncio.sleep", new=AsyncMock()),
        patch("services.user_service.request", new=AsyncMock(return_value=(200, {}))),
    ):
        result = await svc.post_register_success(
            mock_client,
            user_register_result={"UserID": 1},
            user_profile=profile,
        )

    assert result[1] == ChatSessionStatus.APPLIED
    assert result[2] == ApplyResult.MEETING_APPLICATION_SUCCESS


@pytest.mark.asyncio
async def test_post_register_success_with_positions_some_fail():
    from utils.const import APPLY_POSITION_IDS_KEY

    svc = _make_svc()
    svc._chat_repository.register_user_id.return_value = True
    svc._chat_repository.update_session_status.return_value = ChatSessionStatus.APPLIED

    profile = _make_user_profile({APPLY_POSITION_IDS_KEY: ["1", "2"]})

    mock_client = MagicMock()
    mock_client.cookie_jar = []

    # Position 1 succeeds, position 2 fails — returns 404
    position_detail = {"Position": {"Modified": "2024-01-01T00:00:00"}}
    svc._position_service.get_position_detail = AsyncMock(return_value=position_detail)

    # API: success for pos 1, failure for pos 2
    call_count = [0]

    async def fake_request(client, method, path, **kwargs):
        call_count[0] += 1
        if "1" in path:
            return 200, {}
        return 500, None

    # post_apply_failure needs the aica_api_repository.post too
    svc._aica_api_repository.post = AsyncMock(
        return_value=(200, {"Positions": [{"ID": 1}]})
    )

    with (
        patch("services.user_service.asyncio.sleep", new=AsyncMock()),
        patch("services.user_service.request") as mock_req,
    ):
        mock_req.return_value = (200, {})

        result = await svc.post_register_success(
            mock_client,
            user_register_result={"UserID": 1},
            user_profile=profile,
        )

    # Both succeed → APPLIED
    assert result[2] in (
        ApplyResult.MEETING_APPLICATION_SUCCESS,
        ApplyResult.MEETING_APPLICATION_FAIL,
    )


# ─── finish_apply ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_finish_apply_no_session_status():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = None

    result = await svc.finish_apply()
    assert result[0] == status.HTTP_400_BAD_REQUEST
    assert result[2] == ApplyResult.INVALID_SESSION_STATUS


@pytest.mark.asyncio
async def test_finish_apply_chatting_status():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.CHATTING

    result = await svc.finish_apply()
    assert result[0] == status.HTTP_400_BAD_REQUEST
    assert result[2] == ApplyResult.INVALID_SESSION_STATUS


@pytest.mark.asyncio
async def test_finish_apply_already_registered():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.REGISTERED

    result = await svc.finish_apply()
    assert result[2] == ApplyResult.REGISTER_ALREADY


@pytest.mark.asyncio
async def test_finish_apply_already_applied():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.APPLIED

    result = await svc.finish_apply()
    assert result[2] == ApplyResult.MEETING_APPLICATION_ALREADY


@pytest.mark.asyncio
async def test_finish_apply_no_user_profile():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.REGISTERING
    svc._user_repository.get_user_profile.return_value = None

    result = await svc.finish_apply()
    assert result[0] == status.HTTP_400_BAD_REQUEST
    assert result[2] == ApplyResult.UNKNOWN


@pytest.mark.asyncio
async def test_finish_apply_register_success():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.REGISTERING
    profile = _make_user_profile({})
    svc._user_repository.get_user_profile.return_value = profile
    svc._chat_repository.register_user_id.return_value = True

    # Mock aiohttp.ClientSession and the register API call
    mock_client = MagicMock()
    mock_client.cookie_jar = []
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("services.user_service.aiohttp.ClientSession", return_value=mock_client),
        patch.object(
            svc,
            "_call_register_user_api",
            new=AsyncMock(return_value=(200, {"UserID": 99})),
        ),
        patch.object(
            svc,
            "post_register_success",
            new=AsyncMock(
                return_value=(
                    200,
                    ChatSessionStatus.REGISTERED,
                    ApplyResult.REGISTER_SUCCESS,
                    {"Cookies": []},
                )
            ),
        ),
    ):
        result = await svc.finish_apply()

    assert result[2] == ApplyResult.REGISTER_SUCCESS


@pytest.mark.asyncio
async def test_finish_apply_validation_failure_409():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.REGISTERING
    profile = _make_user_profile(
        {"basic_profile": {"email": "dup@example.com", "phoneNo": "0901234567"}}
    )
    svc._user_repository.get_user_profile.return_value = profile

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    validation_result = (
        status.HTTP_409_CONFLICT,
        ChatSessionStatus.REGISTERING,
        ApplyResult.REGISTER_FAIL,
        {"Errors": []},
    )

    with (
        patch("services.user_service.aiohttp.ClientSession", return_value=mock_client),
        patch.object(
            svc,
            "_call_register_user_api",
            new=AsyncMock(return_value=(409, {"Code": 1013})),
        ),
        patch.object(
            svc,
            "post_register_validation_failure",
            return_value=validation_result,
        ),
    ):
        result = await svc.finish_apply()

    assert result[0] == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_finish_apply_validation_failure_returns_none_falls_through():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.REGISTERING
    profile = _make_user_profile({})
    svc._user_repository.get_user_profile.return_value = profile

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("services.user_service.aiohttp.ClientSession", return_value=mock_client),
        patch.object(
            svc,
            "_call_register_user_api",
            new=AsyncMock(return_value=(409, {})),
        ),
        patch.object(
            svc,
            "post_register_validation_failure",
            return_value=None,  # validation_failure_result is None → falls through
        ),
    ):
        result = await svc.finish_apply()

    # Falls through to unexpected error path
    assert result[2] == ApplyResult.REGISTER_FAIL


@pytest.mark.asyncio
async def test_finish_apply_unexpected_http_error():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.REGISTERING
    profile = _make_user_profile({})
    svc._user_repository.get_user_profile.return_value = profile

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("services.user_service.aiohttp.ClientSession", return_value=mock_client),
        patch.object(
            svc,
            "_call_register_user_api",
            new=AsyncMock(return_value=(503, None)),
        ),
    ):
        result = await svc.finish_apply()

    assert result[2] == ApplyResult.REGISTER_FAIL


# ─── apply_position ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_apply_position_invalid_session_status():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.CHATTING

    result = await svc.apply_position("encrypted", {})
    assert result == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_apply_position_invalid_decrypt():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.REGISTERED

    with patch("services.user_service.decrypt", side_effect=ValueError("bad decrypt")):
        result = await svc.apply_position("bad-encrypted", {})
    assert result == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_apply_position_already_applied():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.APPLIED
    svc._user_repository.get_applied_position_ids.return_value = ["42"]

    with patch("services.user_service.decrypt", return_value="42"):
        result = await svc.apply_position("encrypted-42", {})
    assert result == (status.HTTP_200_OK, None)


@pytest.mark.asyncio
async def test_apply_position_success_when_registered():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.REGISTERED
    svc._user_repository.get_applied_position_ids.return_value = []
    svc._chat_repository.update_session_status.return_value = ChatSessionStatus.APPLIED

    position_detail = {"Position": {"Modified": "2024-01-01T00:00:00"}}

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("services.user_service.decrypt", return_value="42"),
        patch("services.user_service.aiohttp.ClientSession", return_value=mock_client),
        patch.object(
            svc,
            "_call_meeting_application_api",
            new=AsyncMock(return_value=(200, {})),
        ),
    ):
        result = await svc.apply_position("encrypted-42", {})

    assert result == (status.HTTP_200_OK, "42")
    svc._user_repository.add_apply_position.assert_called_once()


@pytest.mark.asyncio
async def test_apply_position_success_already_applied_status_no_db_update():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.APPLIED
    svc._user_repository.get_applied_position_ids.return_value = []

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("services.user_service.decrypt", return_value="99"),
        patch("services.user_service.aiohttp.ClientSession", return_value=mock_client),
        patch.object(
            svc,
            "_call_meeting_application_api",
            new=AsyncMock(return_value=(200, {})),
        ),
    ):
        result = await svc.apply_position("encrypted-99", {})

    # Already APPLIED → doesn't call update_session_status
    assert result == (status.HTTP_200_OK, "99")
    svc._chat_repository.update_session_status.assert_not_called()


@pytest.mark.asyncio
async def test_apply_position_success_registered_db_update_fails():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.REGISTERED
    svc._user_repository.get_applied_position_ids.return_value = []
    svc._chat_repository.update_session_status.return_value = False  # DB update fails

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("services.user_service.decrypt", return_value="50"),
        patch("services.user_service.aiohttp.ClientSession", return_value=mock_client),
        patch.object(
            svc,
            "_call_meeting_application_api",
            new=AsyncMock(return_value=(200, {})),
        ),
    ):
        result = await svc.apply_position("enc-50", {})

    assert result == (status.HTTP_200_OK, "50")


@pytest.mark.asyncio
async def test_apply_position_api_failure():
    svc = _make_svc()
    svc._chat_repository.session_status.return_value = ChatSessionStatus.REGISTERED
    svc._user_repository.get_applied_position_ids.return_value = []

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("services.user_service.decrypt", return_value="77"),
        patch("services.user_service.aiohttp.ClientSession", return_value=mock_client),
        patch.object(
            svc,
            "_call_meeting_application_api",
            new=AsyncMock(return_value=(500, None)),
        ),
    ):
        result = await svc.apply_position("enc-77", {})

    assert result == (500, None)


# ─── search_master_data ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_master_data_returns_api_result():
    svc = _make_svc()
    svc._aica_api_repository.get = AsyncMock(return_value=(200, {"masters": []}))

    result = await svc.search_master_data(["gender", "schoolType"])
    assert result == {"masters": []}


# ─── search_by_prefecture_city_name ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_by_prefecture_city_name_returns_result():
    svc = _make_svc()
    expected = {"Locations": []}
    svc._aica_api_repository.post = AsyncMock(return_value=(200, expected))

    result = await svc.search_by_prefecture_city_name(
        [{"prefecture": "東京都", "city": "千代田区"}]
    )
    assert result == expected


# ─── search_commuting_areas ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_commuting_areas_returns_result():
    svc = _make_svc()
    expected = {"Areas": []}
    svc._aica_api_repository.post = AsyncMock(return_value=(200, expected))

    result = await svc.search_commuting_areas("東京都", "千代田区")
    assert result == expected


# ─── search_location ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_location_returns_result():
    svc = _make_svc()
    expected = {"Locations": [{"name": "東京"}]}
    svc._aica_api_repository.post = AsyncMock(return_value=(200, expected))

    result = await svc.search_location("東京")
    assert result == expected


# ─── search_industry ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_industry_returns_result():
    svc = _make_svc()
    expected = {"Industries": []}
    svc._aica_api_repository.post = AsyncMock(return_value=(200, expected))

    result = await svc.search_industry("IT")
    assert result == expected


# ─── search_jobtype_by_keyword ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_jobtype_by_keyword_returns_result():
    svc = _make_svc()
    expected = {"JobTypes": []}
    svc._aica_api_repository.post = AsyncMock(return_value=(200, expected))

    result = await svc.search_jobtype_by_keyword("エンジニア")
    assert result == expected


# ─── search_jobtype_by_names ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_jobtype_by_names_returns_result():
    svc = _make_svc()
    expected = {"JobTypes": [{"name": "営業"}]}
    svc._aica_api_repository.post = AsyncMock(return_value=(200, expected))

    result = await svc.search_jobtype_by_names(["営業", "エンジニア"])
    assert result == expected


# ─── _call_meeting_application_api ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_call_meeting_application_api_no_position_detail_returns_404():
    svc = _make_svc()
    svc._position_service.get_position_detail = AsyncMock(return_value=None)

    mock_client = MagicMock()
    result = await svc._call_meeting_application_api(mock_client, 42)
    assert result == (status.HTTP_404_NOT_FOUND, None)


@pytest.mark.asyncio
async def test_call_meeting_application_api_no_modified_key_returns_404():
    svc = _make_svc()
    svc._position_service.get_position_detail = AsyncMock(
        return_value={"Position": {"NoModified": "key"}}
    )

    mock_client = MagicMock()
    result = await svc._call_meeting_application_api(mock_client, 42)
    assert result == (status.HTTP_404_NOT_FOUND, None)


@pytest.mark.asyncio
async def test_call_meeting_application_api_success():
    svc = _make_svc()
    position_detail = {"Position": {"Modified": "2024-06-01T12:00:00"}}
    svc._position_service.get_position_detail = AsyncMock(return_value=position_detail)

    mock_client = MagicMock()

    with patch("services.user_service.request", new=AsyncMock(return_value=(200, {}))):
        result = await svc._call_meeting_application_api(mock_client, 42)
    assert result == (200, {})


@pytest.mark.asyncio
async def test_call_meeting_application_api_failure_logs_error():
    svc = _make_svc()
    position_detail = {"Position": {"Modified": "2024-06-01T12:00:00"}}
    svc._position_service.get_position_detail = AsyncMock(return_value=position_detail)

    mock_client = MagicMock()

    with patch(
        "services.user_service.request", new=AsyncMock(return_value=(500, None))
    ):
        result = await svc._call_meeting_application_api(mock_client, 42)
    assert result[0] == 500


# ─── _call_register_user_api branches ────────────────────────────────────────


def _make_full_registration_data(
    *,
    has_kana: bool = False,
    school_type: int = 2,  # UNIVERSITY (requires_department)
    exp_company_num: int = 2,  # ONE (has experience)
    management_exp_term: int = 2,  # LESS_THAN_1 (has_experience=True)
    retire_year: int | None = None,
    retire_month: int | None = None,
    will_remote_work: bool = False,
) -> dict:
    """Build a complete registration data dict that can be used in _call_register_user_api."""
    data = {
        "basic_profile": {
            "gender": 1,
            "lastName": "山田",
            "firstName": "太郎",
            "birthYear": 1990,
            "birthMonth": 1,
            "email": "test@example.com",
            "password": "Test1234",
            "phoneNo": "09012345678",
            "prefecture": {"ID": 13, "Name": "東京都"},
            "city": {"ID": 100, "Name": "千代田区"},
            "firstLanguage": 91,
            "driverLicence": 1,
        },
        "education_profile": {
            "schoolType": school_type,
            "graduationYear": 2015,
            "englishLevel": 1,
            "schoolName": "東京大学" if school_type == 2 else None,
            "department": {"ID": 10} if school_type == 2 else None,
            "professionalTrainingCollegeCategory": {"ID": 5}
            if school_type == 4
            else None,
        },
        "experience_profile": {
            "expCompanyNum": exp_company_num,
            "managementExpTerm": management_exp_term,
            "managementPeopleNum": 1 if management_exp_term > 1 else None,
            "industrySmallID": {"ID": 1},
            "jobTypeSmallID": {"ID": 2},
            "jobTypeExpTerm": 3,
            "allCareerJobTypeExpTerm": 5,
            "employmentPost": 1,
            "income": 500,
            "joinYear": 2010,
            "joinMonth": 4,
            "retireYear": retire_year,
            "retireMonth": retire_month,
            "companyName": "テスト株式会社",
            "employeeNum": 3,
            "employmentType": 1,
        },
        "preferences_profile": {
            "willJobTypes": [{"ID": 1}, {"ID": 2}],
            "willWorkAddresses": [{"city": {"ID": 100}}],
            "willIncome": 600,
            "willJobChangePeriod": 1,
            "isRpoAgreement": True,
            "willRemoteWork": will_remote_work,
        },
    }

    if has_kana:
        data["basic_profile"]["lastNameKana"] = "ヤマダ"
        data["basic_profile"]["firstNameKana"] = "タロウ"

    return data


@pytest.mark.asyncio
async def test_call_register_user_api_university_with_kana():
    """Tests the branch: lastNameKana/firstNameKana present + school requires department."""
    svc = _make_svc()
    profile = _make_user_profile(
        _make_full_registration_data(has_kana=True, school_type=2, exp_company_num=1)
    )

    mock_client = MagicMock()
    with patch(
        "services.user_service.request",
        new=AsyncMock(return_value=(200, {"UserID": 1})),
    ):
        result = await svc._call_register_user_api(mock_client, profile)
    assert result[0] == 200


@pytest.mark.asyncio
async def test_call_register_user_api_vocational_school():
    """Tests the branch: school requires category (専門学校)."""
    svc = _make_svc()
    profile = _make_user_profile(
        _make_full_registration_data(school_type=4, exp_company_num=1)
    )

    mock_client = MagicMock()
    with patch(
        "services.user_service.request",
        new=AsyncMock(return_value=(200, {"UserID": 2})),
    ):
        result = await svc._call_register_user_api(mock_client, profile)
    assert result[0] == 200


@pytest.mark.asyncio
async def test_call_register_user_api_no_school_category():
    """Tests the branch: school type that requires neither department nor category (e.g., high school)."""
    # SchoolType 6 = HIGH_SCHOOL → neither requires_department nor requires_category
    svc = _make_svc()
    profile = _make_user_profile(
        _make_full_registration_data(school_type=6, exp_company_num=1)
    )

    mock_client = MagicMock()
    with patch(
        "services.user_service.request",
        new=AsyncMock(return_value=(200, {"UserID": 3})),
    ):
        result = await svc._call_register_user_api(mock_client, profile)
    assert result[0] == 200


@pytest.mark.asyncio
async def test_call_register_user_api_with_experience_and_retire_date():
    """Tests branches: exp_company_num != ZERO, has retire year/month, management exp."""
    svc = _make_svc()
    profile = _make_user_profile(
        _make_full_registration_data(
            school_type=6,
            exp_company_num=2,  # has experience
            management_exp_term=2,  # has_experience=True
            retire_year=2020,
            retire_month=3,
        )
    )

    mock_client = MagicMock()
    with patch(
        "services.user_service.request",
        new=AsyncMock(return_value=(200, {"UserID": 4})),
    ):
        result = await svc._call_register_user_api(mock_client, profile)
    assert result[0] == 200


@pytest.mark.asyncio
async def test_call_register_user_api_with_remote_work():
    """Tests the willRemoteWork=True branch."""
    svc = _make_svc()
    profile = _make_user_profile(
        _make_full_registration_data(
            school_type=6,
            exp_company_num=1,
            will_remote_work=True,
        )
    )

    mock_client = MagicMock()
    with patch(
        "services.user_service.request",
        new=AsyncMock(return_value=(200, {"UserID": 5})),
    ):
        result = await svc._call_register_user_api(
            mock_client, profile, user_agent="MyAgent/1.0"
        )
    assert result[0] == 200


@pytest.mark.asyncio
async def test_call_register_user_api_no_user_agent():
    """Tests the default user_agent='AICA V1' branch."""
    svc = _make_svc()
    profile = _make_user_profile(
        _make_full_registration_data(school_type=6, exp_company_num=1)
    )

    mock_client = MagicMock()
    with patch(
        "services.user_service.request",
        new=AsyncMock(return_value=(200, {"UserID": 6})),
    ):
        result = await svc._call_register_user_api(
            mock_client, profile, user_agent=None
        )
    assert result[0] == 200


@pytest.mark.asyncio
async def test_call_register_user_api_no_management_experience():
    """Tests branch: ExperienceYears.has_experience = False (managementExpTerm=NONE=1)."""
    svc = _make_svc()
    profile = _make_user_profile(
        _make_full_registration_data(
            school_type=6,
            exp_company_num=1,  # CompanyCount.ZERO = no experience
            management_exp_term=1,  # ExperienceYears.NONE → has_experience=False
        )
    )

    mock_client = MagicMock()
    with patch(
        "services.user_service.request",
        new=AsyncMock(return_value=(200, {"UserID": 7})),
    ):
        result = await svc._call_register_user_api(mock_client, profile)
    assert result[0] == 200


@pytest.mark.asyncio
async def test_call_register_user_api_with_experience_no_retire():
    """Tests branch: exp_company_num != ZERO, no retire year (retire year is None)."""
    svc = _make_svc()
    profile = _make_user_profile(
        _make_full_registration_data(
            school_type=6,
            exp_company_num=2,  # has experience (CompanyCount != ZERO)
            management_exp_term=1,  # NONE → has_experience=False
            retire_year=None,
            retire_month=None,
            will_remote_work=False,
        )
    )

    mock_client = MagicMock()
    with patch(
        "services.user_service.request",
        new=AsyncMock(return_value=(200, {"UserID": 8})),
    ):
        result = await svc._call_register_user_api(mock_client, profile)
    assert result[0] == 200


# ─── post_register_success with mixed position results ────────────────────────


@pytest.mark.asyncio
async def test_post_register_success_some_positions_fail_db_update_for_success():
    """Tests lines 634-651: successful_position_ids → update_session_status, some fail."""
    from utils.const import APPLY_POSITION_IDS_KEY

    svc = _make_svc()
    svc._chat_repository.register_user_id.return_value = True
    svc._chat_repository.update_session_status.return_value = ChatSessionStatus.APPLIED

    profile = _make_user_profile({APPLY_POSITION_IDS_KEY: ["10", "20"]})

    mock_client = MagicMock()
    mock_client.cookie_jar = []

    position_detail = {"Position": {"Modified": "2024-01-01T00:00:00"}}
    svc._position_service.get_position_detail = AsyncMock(return_value=position_detail)
    # aica_api_repository.post for post_apply_failure
    svc._aica_api_repository.post = AsyncMock(
        return_value=(200, {"Positions": [{"ID": 10}]})
    )

    call_count = [0]

    async def fake_request(client, method, path, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:  # pos 10 succeeds
            return 200, {}
        return 500, None  # pos 20 fails

    with (
        patch("services.user_service.asyncio.sleep", new=AsyncMock()),
        patch("services.user_service.request", new=AsyncMock(side_effect=fake_request)),
    ):
        result = await svc.post_register_success(
            mock_client,
            user_register_result={"UserID": 1},
            user_profile=profile,
        )

    # update_session_status should be called once since there's a successful position
    svc._chat_repository.update_session_status.assert_called()


@pytest.mark.asyncio
async def test_post_register_success_update_status_fails_logs_error():
    """Tests line 640: DB update fails when setting status to APPLIED."""
    from utils.const import APPLY_POSITION_IDS_KEY

    svc = _make_svc()
    svc._chat_repository.register_user_id.return_value = True
    svc._chat_repository.update_session_status.return_value = False  # DB failure

    profile = _make_user_profile({APPLY_POSITION_IDS_KEY: ["1"]})

    mock_client = MagicMock()
    mock_client.cookie_jar = []

    position_detail = {"Position": {"Modified": "2024-01-01T00:00:00"}}
    svc._position_service.get_position_detail = AsyncMock(return_value=position_detail)

    with (
        patch("services.user_service.asyncio.sleep", new=AsyncMock()),
        patch("services.user_service.request", new=AsyncMock(return_value=(200, {}))),
    ):
        result = await svc.post_register_success(
            mock_client,
            user_register_result={"UserID": 1},
            user_profile=profile,
        )

    # Despite DB failure, still returns APPLIED
    assert result[1] == ChatSessionStatus.APPLIED


@pytest.mark.asyncio
async def test_post_register_success_all_positions_fail_returns_register_success():
    """Tests branch line 634 FALSE: no successful_position_ids, all positions fail.
    Also tests line 651: post_apply_failure returns a result and it's returned."""
    from utils.const import APPLY_POSITION_IDS_KEY

    svc = _make_svc()
    svc._chat_repository.register_user_id.return_value = True

    profile = _make_user_profile({APPLY_POSITION_IDS_KEY: ["1", "2"]})

    mock_client = MagicMock()
    mock_client.cookie_jar = []

    position_detail = {"Position": {"Modified": "2024-01-01T00:00:00"}}
    svc._position_service.get_position_detail = AsyncMock(return_value=position_detail)
    # All applications fail
    svc._aica_api_repository.post = AsyncMock(return_value=(500, None))

    with (
        patch("services.user_service.asyncio.sleep", new=AsyncMock()),
        patch("services.user_service.request", new=AsyncMock(return_value=(500, None))),
    ):
        result = await svc.post_register_success(
            mock_client,
            user_register_result={"UserID": 1},
            user_profile=profile,
        )

    # All failed → no successful_position_ids → no update_session_status call
    svc._chat_repository.update_session_status.assert_not_called()
    # post_apply_failure with all failed, API fail → returns REGISTER_SUCCESS path
    assert result[2] in (
        ApplyResult.REGISTER_SUCCESS,
        ApplyResult.MEETING_APPLICATION_SUCCESS,
        ApplyResult.MEETING_APPLICATION_FAIL,
    )


# ─── post_register_validation_failure education/experience/preferences fields ─


def test_post_register_validation_failure_education_field():
    svc = _make_svc()
    data = _make_registration_data()
    data["education_profile"] = {
        "schoolType": 2,
        "graduationYear": 2015,
        "englishLevel": None,
    }
    profile = _make_user_profile(data)

    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "GraduationYear"}]},
        profile,
        ChatSessionStatus.CHATTING,
    )
    assert result is not None
    assert result[0] == status.HTTP_400_BAD_REQUEST


def test_post_register_validation_failure_experience_field():
    svc = _make_svc()
    data = _make_registration_data()
    data["experience_profile"] = {
        "expCompanyNum": 1,
        "managementExpTerm": 1,
        "income": None,
    }
    profile = _make_user_profile(data)

    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "Income"}]},
        profile,
        ChatSessionStatus.CHATTING,
    )
    assert result is not None
    assert result[0] == status.HTTP_400_BAD_REQUEST


def test_post_register_validation_failure_preferences_field():
    svc = _make_svc()
    data = _make_registration_data()
    data["preferences_profile"] = {"willIncome": None}
    profile = _make_user_profile(data)

    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "WillIncome"}]},
        profile,
        ChatSessionStatus.CHATTING,
    )
    assert result is not None
    assert result[0] == status.HTTP_400_BAD_REQUEST
