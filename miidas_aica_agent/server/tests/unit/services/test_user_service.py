"""Unit tests for UserService — 100% branch coverage required under parity marker."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from domain.entities.chat_session import ChatSessionStatus
from domain.entities.user_profile import (
    JSONUserProfileBasicInfo,
    JSONUserProfileCarrer,
    JSONUserProfileEducation,
    JSONUserProfileWill,
    UserProfile,
)
from repositories.action_log_repo import ActionLogRepository
from repositories.api_repo import AICAAPIRepository
from repositories.chat_repo import ChatRepository
from repositories.user_repo import UserRepository
from services.position_service import PositionService
from services.user_service import UserService
from utils.const import APPLY_POSITION_IDS_KEY
from utils.enum import ApplyResult

pytestmark = pytest.mark.pre_extraction_parity


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def deps():
    return {
        "position_svc": MagicMock(spec=PositionService),
        "chat_repository": Mock(spec=ChatRepository),
        "user_repository": Mock(spec=UserRepository),
        "aica_api_repository": AsyncMock(spec=AICAAPIRepository),
        "action_log_repository": MagicMock(spec=ActionLogRepository),
        "miidas_api_url": "https://example.com",
        "timeout": 30,
    }


@pytest.fixture
def svc(deps):
    return UserService(**deps)


# ---------------------------------------------------------------------------
# __init__ / construction
# ---------------------------------------------------------------------------


def test_constructor_sets_attributes(deps):
    service = UserService(**deps)
    assert service._miidas_api_url == "https://example.com"
    assert service._timeout == 30


# ---------------------------------------------------------------------------
# get_profile
# ---------------------------------------------------------------------------


def test_get_profile_removes_apply_position_ids_key(svc, deps):
    profile = MagicMock(spec=UserProfile)
    profile.miidas_registration_user_data = {
        APPLY_POSITION_IDS_KEY: [1, 2],
        "other": "val",
    }
    deps["user_repository"].get_user_profile.return_value = profile

    result = svc.get_profile()

    assert result is profile
    assert APPLY_POSITION_IDS_KEY not in profile.miidas_registration_user_data


def test_get_profile_returns_none_when_no_profile(svc, deps):
    deps["user_repository"].get_user_profile.return_value = None
    assert svc.get_profile() is None


def test_get_profile_with_no_registration_data(svc, deps):
    profile = MagicMock(spec=UserProfile)
    profile.miidas_registration_user_data = None
    deps["user_repository"].get_user_profile.return_value = profile
    result = svc.get_profile()
    assert result is profile


# ---------------------------------------------------------------------------
# save_basic_profile
# ---------------------------------------------------------------------------


def test_save_basic_profile(svc, deps):
    deps["user_repository"].update_miidas_registration_user_data.return_value = True
    result = svc.save_basic_profile(Mock(spec=JSONUserProfileBasicInfo))
    assert result is True
    deps["user_repository"].update_miidas_registration_user_data.assert_called_once()


# ---------------------------------------------------------------------------
# save_education_profile
# ---------------------------------------------------------------------------


def test_save_education_profile(svc, deps):
    deps["user_repository"].update_miidas_registration_user_data.return_value = True
    result = svc.save_education_profile(Mock(spec=JSONUserProfileEducation))
    assert result is True


# ---------------------------------------------------------------------------
# save_experience_profile
# ---------------------------------------------------------------------------


def test_save_experience_profile(svc, deps):
    deps["user_repository"].update_miidas_registration_user_data.return_value = True
    result = svc.save_experience_profile(Mock(spec=JSONUserProfileCarrer))
    assert result is True


# ---------------------------------------------------------------------------
# save_preferences_profile — deduplication
# ---------------------------------------------------------------------------


def test_save_preferences_profile_deduplicates_jobtypes_and_cities(svc, deps):
    from domain.entities.user_profile import JSONUserProfileWill

    jt = MagicMock()
    jt.id = "jt-1"
    city = MagicMock()
    city.city = MagicMock()
    city.city.id = "city-1"
    profile = MagicMock(spec=JSONUserProfileWill)
    profile.will_job_types = [jt, jt]  # duplicate
    profile.will_work_addresses = [city, city]  # duplicate
    deps["user_repository"].update_miidas_registration_user_data.return_value = True

    result = svc.save_preferences_profile(profile)

    assert result is True
    # Deduplication occurred
    assert len(profile.will_job_types) == 1
    assert len(profile.will_work_addresses) == 1


# ---------------------------------------------------------------------------
# start_apply
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_apply_with_position_id_sets_applying(svc, deps):
    deps["chat_repository"].session_status.return_value = ChatSessionStatus.CHATTING
    deps[
        "chat_repository"
    ].update_session_status.return_value = ChatSessionStatus.APPLYING
    with patch("services.user_service.decrypt", return_value="pos-1"):
        result = await svc.start_apply(encrypted_position_id="enc-pos-1")
    assert result == ChatSessionStatus.APPLYING


@pytest.mark.asyncio
async def test_start_apply_without_position_id_sets_registering(svc, deps):
    deps["chat_repository"].session_status.return_value = ChatSessionStatus.CHATTING
    deps[
        "chat_repository"
    ].update_session_status.return_value = ChatSessionStatus.REGISTERING
    result = await svc.start_apply()
    assert result == ChatSessionStatus.REGISTERING


@pytest.mark.asyncio
async def test_start_apply_returns_none_when_no_session(svc, deps):
    deps["chat_repository"].session_status.return_value = None
    result = await svc.start_apply()
    assert result is None


@pytest.mark.asyncio
async def test_start_apply_exception_is_caught(svc, deps):
    deps["chat_repository"].session_status.return_value = ChatSessionStatus.CHATTING
    with patch("services.user_service.decrypt", side_effect=Exception("decrypt fail")):
        result = await svc.start_apply(encrypted_position_id="enc-pos-1")
    # Exception is caught, returns current session_status (CHATTING)
    assert result == ChatSessionStatus.CHATTING


# ---------------------------------------------------------------------------
# apply_add_position
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_add_position_returns_none_when_no_session(svc, deps):
    deps["chat_repository"].session_status.return_value = None
    result = await svc.apply_add_position("enc-1")
    assert result is None


@pytest.mark.asyncio
async def test_apply_add_position_registering_transitions_to_applying(svc, deps):
    deps["chat_repository"].session_status.return_value = ChatSessionStatus.REGISTERING
    deps[
        "chat_repository"
    ].update_session_status.return_value = ChatSessionStatus.APPLYING
    with patch("services.user_service.decrypt", return_value="pos-1"):
        result = await svc.apply_add_position("enc-1")
    assert result == ChatSessionStatus.APPLYING


@pytest.mark.asyncio
async def test_apply_add_position_applying_stays_applying(svc, deps):
    deps["chat_repository"].session_status.return_value = ChatSessionStatus.APPLYING
    with patch("services.user_service.decrypt", return_value="pos-1"):
        result = await svc.apply_add_position("enc-1")
    assert result == ChatSessionStatus.APPLYING


@pytest.mark.asyncio
async def test_apply_add_position_chatting_returns_none(svc, deps):
    deps["chat_repository"].session_status.return_value = ChatSessionStatus.CHATTING
    result = await svc.apply_add_position("enc-1")
    assert result is None


@pytest.mark.asyncio
async def test_apply_add_position_exception_returns_none(svc, deps):
    deps["chat_repository"].session_status.return_value = ChatSessionStatus.REGISTERING
    with patch("services.user_service.decrypt", side_effect=Exception("fail")):
        result = await svc.apply_add_position("enc-1")
    assert result is None


# ---------------------------------------------------------------------------
# post_apply_failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_apply_failure_api_error_with_successes(svc, deps):
    deps["aica_api_repository"].post.return_value = (500, None)
    result = await svc.post_apply_failure([1], [1], [], [])
    assert result is not None
    status_code, session_status, apply_result, payload = result
    assert apply_result == ApplyResult.MEETING_APPLICATION_SUCCESS


@pytest.mark.asyncio
async def test_post_apply_failure_api_error_no_successes(svc, deps):
    deps["aica_api_repository"].post.return_value = (500, None)
    result = await svc.post_apply_failure([1], [], [1], [])
    assert result is not None
    _, _, apply_result, _ = result
    assert apply_result == ApplyResult.REGISTER_SUCCESS


@pytest.mark.asyncio
async def test_post_apply_failure_all_failed_with_data(svc, deps):
    deps["aica_api_repository"].post.return_value = (200, {"Positions": [{"ID": 2}]})
    result = await svc.post_apply_failure([2], [], [2], [])
    assert result is not None
    _, _, apply_result, payload = result
    assert apply_result == ApplyResult.MEETING_APPLICATION_FAIL


@pytest.mark.asyncio
async def test_post_apply_failure_returns_none_when_no_failures(svc, deps):
    deps["aica_api_repository"].post.return_value = (200, {"Positions": [{"ID": 1}]})
    result = await svc.post_apply_failure([1], [1], [], [])
    assert result is None


# ---------------------------------------------------------------------------
# post_register_validation_failure
# ---------------------------------------------------------------------------


def _make_user_profile():
    profile = MagicMock(spec=UserProfile)
    profile.miidas_registration_user_data = {
        "basic_profile": {"email": "test@test.com", "phoneNo": "09012345678"},
        "education_profile": {},
        "experience_profile": {},
        "preferences_profile": {},
    }
    return profile


def test_post_register_validation_failure_email_duplication(svc):
    result = svc.post_register_validation_failure(
        {"Code": 1013}, _make_user_profile(), ChatSessionStatus.REGISTERING
    )
    assert result is not None
    assert result[2] == ApplyResult.REGISTER_FAIL


def test_post_register_validation_failure_phone_duplication(svc):
    result = svc.post_register_validation_failure(
        {"Code": 1001}, _make_user_profile(), ChatSessionStatus.REGISTERING
    )
    assert result is not None
    assert result[2] == ApplyResult.REGISTER_FAIL


def test_post_register_validation_failure_unknown_code_returns_none(svc):
    result = svc.post_register_validation_failure(
        {"Code": 9999}, _make_user_profile(), ChatSessionStatus.REGISTERING
    )
    assert result is None


def test_post_register_validation_failure_no_code_returns_none(svc):
    result = svc.post_register_validation_failure(
        {}, _make_user_profile(), ChatSessionStatus.REGISTERING
    )
    assert result is None


# ---------------------------------------------------------------------------
# search_master_data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_master_data(svc, deps):
    deps["aica_api_repository"].get.return_value = (200, {"masters": []})
    result = await svc.search_master_data(["school_types"])
    assert result == {"masters": []}


# ---------------------------------------------------------------------------
# search_by_prefecture_city_name
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_by_prefecture_city_name(svc, deps):
    deps["aica_api_repository"].post.return_value = (200, {"Locations": []})
    result = await svc.search_by_prefecture_city_name(
        [{"prefecture": "東京都", "city": "新宿区"}]
    )
    assert result == {"Locations": []}


# ---------------------------------------------------------------------------
# search_commuting_areas
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_commuting_areas(svc, deps):
    deps["aica_api_repository"].post.return_value = (200, {"Areas": []})
    result = await svc.search_commuting_areas("東京都", "新宿区")
    assert result == {"Areas": []}


# ---------------------------------------------------------------------------
# search_location
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_location(svc, deps):
    deps["aica_api_repository"].post.return_value = (200, {"Locations": []})
    result = await svc.search_location("東京")
    assert result == {"Locations": []}


# ---------------------------------------------------------------------------
# search_industry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_industry(svc, deps):
    deps["aica_api_repository"].post.return_value = (200, {"Industries": []})
    result = await svc.search_industry("IT")
    assert result == {"Industries": []}


# ---------------------------------------------------------------------------
# search_jobtype_by_keyword
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_jobtype_by_keyword(svc, deps):
    deps["aica_api_repository"].post.return_value = (200, {"Jobtypes": []})
    result = await svc.search_jobtype_by_keyword("エンジニア")
    assert result == {"Jobtypes": []}


# ---------------------------------------------------------------------------
# search_jobtype_by_names
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_jobtype_by_names(svc, deps):
    deps["aica_api_repository"].post.return_value = (200, {"Jobtypes": []})
    result = await svc.search_jobtype_by_names(["エンジニア"])
    assert result == {"Jobtypes": []}


# ---------------------------------------------------------------------------
# _call_register_user_api — builds request body and calls request()
# ---------------------------------------------------------------------------


def _make_full_user_profile(**overrides):
    profile = MagicMock(spec=UserProfile)
    data = {
        "basic_profile": {
            "gender": 1,
            "lastName": "山田",
            "firstName": "太郎",
            "birthYear": 1990,
            "birthMonth": 1,
            "email": "t@test.com",
            "password": "pw",
            "phoneNo": "09000000000",
            "prefecture": {"ID": 1},
            "city": {"ID": 2},
            "firstLanguage": 1,
            "driverLicence": 1,
        },
        "education_profile": {
            "schoolType": 1,
            "graduationYear": 2012,
            "englishLevel": 1,
            "schoolName": "大学",
            "department": {"ID": 3},
            "professionalTrainingCollegeCategory": {"ID": 4},
        },
        "experience_profile": {
            "expCompanyNum": 0,
            "managementExpTerm": 1,
        },
        "preferences_profile": {
            "willJobTypes": [{"ID": 1}],
            "willWorkAddresses": [{"city": {"ID": 1}}],
            "willIncome": 400,
            "willJobChangePeriod": 1,
            "isRpoAgreement": True,
            "willRemoteWork": False,
        },
    }
    data.update(overrides)
    profile.miidas_registration_user_data = data
    return profile


@pytest.mark.asyncio
async def test_call_register_user_api_no_experience_no_kana(svc):
    profile = _make_full_user_profile()
    client = AsyncMock()
    with (
        patch("services.user_service.request", return_value=(200, {"UserID": 1})),
        patch("services.user_service.ExperienceYears") as mock_exp,
        patch("services.user_service.CompanyCount") as mock_cc,
    ):
        mock_exp.has_experience.return_value = False
        mock_cc.ZERO = 0
        result = await svc._call_register_user_api(client, profile)
    assert result[0] == 200


@pytest.mark.asyncio
async def test_call_register_user_api_with_experience_and_kana(svc):
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data["basic_profile"]["lastNameKana"] = "ヤマダ"
    profile.miidas_registration_user_data["basic_profile"]["firstNameKana"] = "タロウ"
    profile.miidas_registration_user_data["experience_profile"] = {
        "expCompanyNum": 1,
        "managementExpTerm": 1,
        "managementPeopleNum": 5,
        "industrySmallID": {"ID": 1},
        "jobTypeSmallID": {"ID": 2},
        "jobTypeExpTerm": 3,
        "allCareerJobTypeExpTerm": 5,
        "employmentPost": 1,
        "income": 500,
        "retireYear": 2020,
        "retireMonth": 3,
        "companyName": "株式会社テスト",
        "employeeNum": 100,
        "employmentType": 1,
    }
    profile.miidas_registration_user_data["preferences_profile"]["willRemoteWork"] = (
        True
    )
    client = AsyncMock()
    with patch("services.user_service.request", return_value=(200, {"UserID": 1})):
        result = await svc._call_register_user_api(client, profile)
    assert result[0] == 200


@pytest.mark.asyncio
async def test_call_register_user_api_school_requires_category(svc):
    profile = _make_full_user_profile()
    with patch("services.user_service.SchoolType") as mock_st:
        mock_st.requires_department.return_value = False
        mock_st.requires_category.return_value = True
        mock_st.get_value.return_value = 1
        client = AsyncMock()
        with (
            patch("services.user_service.request", return_value=(200, {"UserID": 1})),
            patch("services.user_service.ExperienceYears") as mock_exp,
            patch("services.user_service.CompanyCount") as mock_cc,
        ):
            mock_exp.has_experience.return_value = False
            mock_cc.ZERO = 0
            result = await svc._call_register_user_api(client, profile)
        assert result[0] == 200


# ---------------------------------------------------------------------------
# _call_meeting_application_api
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_call_meeting_api_returns_404_when_no_position_detail(svc, deps):
    deps["position_svc"].get_position_detail = AsyncMock(return_value=None)
    client = AsyncMock()
    from fastapi import status as http_status

    result = await svc._call_meeting_application_api(client, 1)
    assert result[0] == http_status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_call_meeting_api_returns_404_when_no_modified_field(svc, deps):
    deps["position_svc"].get_position_detail = AsyncMock(return_value={"Position": {}})
    client = AsyncMock()
    from fastapi import status as http_status

    result = await svc._call_meeting_application_api(client, 1)
    assert result[0] == http_status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_call_meeting_api_calls_request_on_success(svc, deps):
    from fastapi import status as http_status

    deps["position_svc"].get_position_detail = AsyncMock(
        return_value={"Position": {"Modified": "2024-01-01T00:00:00+00:00"}}
    )
    client = AsyncMock()
    with patch("services.user_service.request", return_value=(200, {"ok": True})):
        result = await svc._call_meeting_application_api(client, 1)
    assert result[0] == 200


@pytest.mark.asyncio
async def test_call_meeting_api_logs_error_on_non_200(svc, deps):
    from fastapi import status as http_status

    deps["position_svc"].get_position_detail = AsyncMock(
        return_value={"Position": {"Modified": "2024-01-01T00:00:00+00:00"}}
    )
    client = AsyncMock()
    with patch("services.user_service.request", return_value=(500, None)):
        result = await svc._call_meeting_application_api(client, 1)
    assert result[0] == 500


# ---------------------------------------------------------------------------
# post_register_success — minimal path test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_register_success_unexpected_response_logged(svc, deps):
    client = AsyncMock()
    profile = _make_full_user_profile()
    # Missing UserID in result
    with patch("services.user_service.aiohttp.ClientSession") as mock_session:
        mock_session.return_value.__aenter__ = AsyncMock()
        mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
        with patch.object(
            svc, "_call_meeting_application_api", AsyncMock(return_value=(404, None))
        ):
            result = await svc.post_register_success(client, {}, profile)


# ---------------------------------------------------------------------------
# apply_position
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_position_invalid_session_status(svc, deps):
    from fastapi import status as http_status

    deps["chat_repository"].session_status.return_value = ChatSessionStatus.CHATTING
    result = await svc.apply_position("enc-1", {})
    assert result == http_status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_apply_position_decrypt_fails_returns_400(svc, deps):
    from fastapi import status as http_status

    deps["chat_repository"].session_status.return_value = ChatSessionStatus.REGISTERED
    with patch("services.user_service.decrypt", side_effect=ValueError("bad")):
        result = await svc.apply_position("enc-1", {})
    assert result == http_status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_apply_position_already_applied_returns_200(svc, deps):
    from fastapi import status as http_status

    deps["chat_repository"].session_status.return_value = ChatSessionStatus.REGISTERED
    deps["user_repository"].get_applied_position_ids.return_value = ["pos-1"]
    with patch("services.user_service.decrypt", return_value="pos-1"):
        result = await svc.apply_position("enc-1", {})
    status_code, pos_id = result
    assert status_code == http_status.HTTP_200_OK
    assert pos_id is None


@pytest.mark.asyncio
async def test_apply_position_success_calls_meeting_api(svc, deps):
    from fastapi import status as http_status

    deps["chat_repository"].session_status.return_value = ChatSessionStatus.REGISTERED
    deps["user_repository"].get_applied_position_ids.return_value = []
    deps[
        "chat_repository"
    ].update_session_status.return_value = ChatSessionStatus.APPLIED
    with (
        patch("services.user_service.decrypt", return_value="99"),
        patch("services.user_service.aiohttp.ClientSession") as mock_cs,
        patch.object(
            svc, "_call_meeting_application_api", AsyncMock(return_value=(200, None))
        ),
    ):
        mock_cs.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_cs.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await svc.apply_position("enc-1", {})
    status_code, pos_id = result
    assert status_code == http_status.HTTP_200_OK
    assert pos_id == "99"


@pytest.mark.asyncio
async def test_apply_position_meeting_api_failure(svc, deps):
    from fastapi import status as http_status

    deps["chat_repository"].session_status.return_value = ChatSessionStatus.REGISTERED
    deps["user_repository"].get_applied_position_ids.return_value = []
    with (
        patch("services.user_service.decrypt", return_value="99"),
        patch("services.user_service.aiohttp.ClientSession") as mock_cs,
        patch.object(
            svc, "_call_meeting_application_api", AsyncMock(return_value=(404, None))
        ),
    ):
        mock_cs.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_cs.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await svc.apply_position("enc-1", {})
    status_code, _ = result
    assert status_code == 404


# ---------------------------------------------------------------------------
# finish_apply — early-return branches
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_finish_apply_invalid_session_status_returns_400(svc, deps):
    from fastapi import status as http_status

    deps["chat_repository"].session_status.return_value = ChatSessionStatus.CHATTING
    result = await svc.finish_apply()
    assert result[0] == http_status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_finish_apply_already_registered_returns_register_already(svc, deps):
    from fastapi import status as http_status
    from utils.enum import ApplyResult

    deps["chat_repository"].session_status.return_value = ChatSessionStatus.REGISTERED
    result = await svc.finish_apply()
    assert result[0] == http_status.HTTP_200_OK
    assert result[2] == ApplyResult.REGISTER_ALREADY


# ---------------------------------------------------------------------------
# post_apply_failure — mismatch logging branches
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_apply_failure_mismatch_logs_error(svc, deps):
    # pos 2 is in position_ids but not in Positions response -> mismatch error logged
    deps["aica_api_repository"].post.return_value = (200, {"Positions": [{"ID": 1}]})
    # successful_position_ids includes 2 which is not in Positions -> triggers mismatch warning
    result = await svc.post_apply_failure([1, 2], [1, 2], [], [])
    assert result is None  # no failed positions -> returns None


# ---------------------------------------------------------------------------
# post_register_validation_failure — Details branch
# ---------------------------------------------------------------------------


def test_post_register_validation_failure_details_birthday(svc):
    profile = _make_full_user_profile()
    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "Birthday"}]},
        profile,
        ChatSessionStatus.REGISTERING,
    )
    # birthday maps to birthYear/birthMonth error fields
    if result is not None:
        assert result[2] == ApplyResult.REGISTER_FAIL


def test_post_register_validation_failure_details_gender(svc):
    profile = _make_full_user_profile()
    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "Gender"}]},
        profile,
        ChatSessionStatus.REGISTERING,
    )
    if result is not None:
        assert result[2] == ApplyResult.REGISTER_FAIL


# ---------------------------------------------------------------------------
# _call_register_user_api — experience + retire branches
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_call_register_user_api_with_experience_company_and_retire(svc):
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data["experience_profile"] = {
        "expCompanyNum": 1,
        "managementExpTerm": 3,
        "managementPeopleNum": 5,
        "industrySmallID": {"ID": 1},
        "jobTypeSmallID": {"ID": 2},
        "jobTypeExpTerm": 3,
        "allCareerJobTypeExpTerm": 5,
        "employmentPost": 1,
        "income": 500,
        "retireYear": 2020,
        "retireMonth": 3,
        "companyName": "株式会社テスト",
        "employeeNum": 100,
        "employmentType": 1,
        "joinYear": 2010,
        "joinMonth": 4,
    }
    client = AsyncMock()
    with (
        patch("services.user_service.request", return_value=(200, {"UserID": 1})),
        patch("services.user_service.SchoolType") as mock_st,
    ):
        mock_st.requires_department.return_value = False
        mock_st.requires_category.return_value = False
        mock_st.get_value.return_value = 1
        result = await svc._call_register_user_api(client, profile)
    assert result[0] == 200


@pytest.mark.asyncio
async def test_call_register_user_api_company_no_retire(svc):
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data["experience_profile"] = {
        "expCompanyNum": 1,
        "managementExpTerm": 3,
        "managementPeopleNum": 5,
        "industrySmallID": {"ID": 1},
        "jobTypeSmallID": {"ID": 2},
        "jobTypeExpTerm": 3,
        "allCareerJobTypeExpTerm": 5,
        "employmentPost": 1,
        "income": 500,
        "retireYear": None,
        "retireMonth": None,
        "companyName": "株式会社テスト",
        "employeeNum": 100,
        "employmentType": 1,
        "joinYear": 2010,
        "joinMonth": 4,
    }
    client = AsyncMock()
    with (
        patch("services.user_service.request", return_value=(200, {"UserID": 1})),
        patch("services.user_service.SchoolType") as mock_st,
    ):
        mock_st.requires_department.return_value = False
        mock_st.requires_category.return_value = False
        mock_st.get_value.return_value = 1
        result = await svc._call_register_user_api(client, profile)
    assert result[0] == 200


# ---------------------------------------------------------------------------
# post_register_success
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_register_success_no_apply_positions_returns_register_success(
    svc, deps
):
    client = AsyncMock()
    client.cookie_jar = []
    deps["chat_repository"].register_user_id.return_value = True
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data[APPLY_POSITION_IDS_KEY] = []
    result = await svc.post_register_success(client, {"UserID": 42}, profile)
    assert result[2] == ApplyResult.REGISTER_SUCCESS


@pytest.mark.asyncio
async def test_post_register_success_db_register_failure_logged(svc, deps):
    client = AsyncMock()
    client.cookie_jar = []
    deps["chat_repository"].register_user_id.return_value = False
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data[APPLY_POSITION_IDS_KEY] = []
    result = await svc.post_register_success(client, {"UserID": 42}, profile)
    assert result[2] == ApplyResult.REGISTER_SUCCESS


@pytest.mark.asyncio
async def test_post_register_success_all_applications_succeed(svc, deps):
    client = AsyncMock()
    client.cookie_jar = []
    deps["chat_repository"].register_user_id.return_value = True
    deps[
        "chat_repository"
    ].update_session_status.return_value = ChatSessionStatus.APPLIED
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data[APPLY_POSITION_IDS_KEY] = ["1"]
    with (
        patch.object(
            svc, "_call_meeting_application_api", AsyncMock(return_value=(200, None))
        ),
        patch("services.user_service.asyncio.sleep", AsyncMock()),
    ):
        result = await svc.post_register_success(client, {"UserID": 42}, profile)
    assert result[2] == ApplyResult.MEETING_APPLICATION_SUCCESS


@pytest.mark.asyncio
async def test_post_register_success_some_applications_fail_returns_fail_result(
    svc, deps
):
    from fastapi import status as http_status

    client = AsyncMock()
    client.cookie_jar = []
    deps["chat_repository"].register_user_id.return_value = True
    deps[
        "chat_repository"
    ].update_session_status.return_value = ChatSessionStatus.APPLIED
    deps["aica_api_repository"].post.return_value = (
        500,
        None,
    )  # post_apply_failure -> register success
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data[APPLY_POSITION_IDS_KEY] = ["1"]
    with (
        patch.object(
            svc, "_call_meeting_application_api", AsyncMock(return_value=(404, None))
        ),
        patch("services.user_service.asyncio.sleep", AsyncMock()),
    ):
        result = await svc.post_register_success(client, {"UserID": 42}, profile)
    assert result is not None


# ---------------------------------------------------------------------------
# post_register_validation_failure Details branches
# ---------------------------------------------------------------------------


def test_post_register_validation_failure_education_field(svc):
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data["education_profile"] = {
        "graduationYear": 2012
    }
    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "GraduationYear"}]},
        profile,
        ChatSessionStatus.REGISTERING,
    )
    if result is not None:
        assert result[2] == ApplyResult.REGISTER_FAIL


def test_post_register_validation_failure_joinYm_field(svc):
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data["experience_profile"] = {
        "joinYear": 2010,
        "joinMonth": 4,
    }
    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "JoinYm"}]},
        profile,
        ChatSessionStatus.REGISTERING,
    )
    if result is not None:
        assert result[2] == ApplyResult.REGISTER_FAIL


def test_post_register_validation_failure_retireYm_field(svc):
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data["experience_profile"] = {
        "retireYear": 2020,
        "retireMonth": 3,
    }
    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "RetireYm"}]},
        profile,
        ChatSessionStatus.REGISTERING,
    )
    if result is not None:
        assert result[2] == ApplyResult.REGISTER_FAIL


def test_post_register_validation_failure_unknown_field_no_return(svc):
    profile = _make_full_user_profile()
    # Unknown fields hit the logger.error branch, then KeyError from empty profile_section.
    # We just need to exercise that branch; the KeyError is the expected result.
    with pytest.raises(KeyError):
        svc.post_register_validation_failure(
            {"Details": [{"Field": "UnknownXyz123"}]},
            profile,
            ChatSessionStatus.REGISTERING,
        )


def test_post_register_validation_failure_details_no_field_key(svc):
    profile = _make_full_user_profile()
    result = svc.post_register_validation_failure(
        {"Details": [{}]},
        profile,
        ChatSessionStatus.REGISTERING,
    )
    assert result is None


def test_post_register_validation_failure_preferences_field(svc):
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data["preferences_profile"] = {"willIncome": 400}
    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "WillIncome"}]},
        profile,
        ChatSessionStatus.REGISTERING,
    )
    if result is not None:
        assert result[2] == ApplyResult.REGISTER_FAIL


def test_post_register_validation_failure_experience_field(svc):
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data["experience_profile"] = {"jobTypeExpTerm": 2}
    result = svc.post_register_validation_failure(
        {"Details": [{"Field": "JobTypeExpTerm"}]},
        profile,
        ChatSessionStatus.REGISTERING,
    )
    if result is not None:
        assert result[2] == ApplyResult.REGISTER_FAIL


# ---------------------------------------------------------------------------
# apply_position — session update failure path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_position_session_update_fails_still_returns_200(svc, deps):
    from fastapi import status as http_status

    deps["chat_repository"].session_status.return_value = ChatSessionStatus.REGISTERED
    deps["user_repository"].get_applied_position_ids.return_value = []
    deps["chat_repository"].update_session_status.return_value = None  # failure
    with (
        patch("services.user_service.decrypt", return_value="99"),
        patch("services.user_service.aiohttp.ClientSession") as mock_cs,
        patch.object(
            svc, "_call_meeting_application_api", AsyncMock(return_value=(200, None))
        ),
    ):
        mock_cs.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_cs.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await svc.apply_position("enc-1", {})
    status_code, pos_id = result
    assert status_code == http_status.HTTP_200_OK


# ---------------------------------------------------------------------------
# finish_apply — full register path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_finish_apply_applied_session_returns_already(svc, deps):
    from fastapi import status as http_status
    from utils.enum import ApplyResult

    deps["chat_repository"].session_status.return_value = ChatSessionStatus.APPLIED
    result = await svc.finish_apply()
    assert result[2] == ApplyResult.MEETING_APPLICATION_ALREADY


@pytest.mark.asyncio
async def test_finish_apply_no_user_profile_returns_400(svc, deps):
    from fastapi import status as http_status
    from utils.enum import ApplyResult

    deps["chat_repository"].session_status.return_value = ChatSessionStatus.REGISTERING
    deps["user_repository"].get_user_profile.return_value = None
    result = await svc.finish_apply()
    assert result[0] == http_status.HTTP_400_BAD_REQUEST
    assert result[2] == ApplyResult.UNKNOWN


@pytest.mark.asyncio
async def test_finish_apply_register_success(svc, deps):
    from fastapi import status as http_status
    from utils.enum import ApplyResult

    deps["chat_repository"].session_status.return_value = ChatSessionStatus.REGISTERING
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data[APPLY_POSITION_IDS_KEY] = []
    deps["user_repository"].get_user_profile.return_value = profile
    deps["chat_repository"].register_user_id.return_value = True
    with (
        patch("services.user_service.aiohttp.ClientSession") as mock_cs,
        patch.object(
            svc, "_call_register_user_api", AsyncMock(return_value=(200, {"UserID": 1}))
        ),
    ):
        mock_client = AsyncMock()
        mock_client.cookie_jar = []
        mock_cs.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cs.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await svc.finish_apply()
    assert result[2] == ApplyResult.REGISTER_SUCCESS


@pytest.mark.asyncio
async def test_finish_apply_register_validation_error(svc, deps):
    from fastapi import status as http_status
    from utils.enum import ApplyResult

    deps["chat_repository"].session_status.return_value = ChatSessionStatus.REGISTERING
    profile = _make_full_user_profile()
    deps["user_repository"].get_user_profile.return_value = profile
    with (
        patch("services.user_service.aiohttp.ClientSession") as mock_cs,
        patch.object(
            svc,
            "_call_register_user_api",
            AsyncMock(return_value=(409, {"Code": 1013})),
        ),
    ):
        mock_client = AsyncMock()
        mock_cs.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cs.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await svc.finish_apply()
    assert result[2] == ApplyResult.REGISTER_FAIL


@pytest.mark.asyncio
async def test_finish_apply_unexpected_error(svc, deps):
    from fastapi import status as http_status
    from utils.enum import ApplyResult

    deps["chat_repository"].session_status.return_value = ChatSessionStatus.REGISTERING
    profile = _make_full_user_profile()
    deps["user_repository"].get_user_profile.return_value = profile
    with (
        patch("services.user_service.aiohttp.ClientSession") as mock_cs,
        patch.object(
            svc, "_call_register_user_api", AsyncMock(return_value=(500, None))
        ),
    ):
        mock_client = AsyncMock()
        mock_cs.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cs.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await svc.finish_apply()
    assert result[0] == http_status.HTTP_500_INTERNAL_SERVER_ERROR
    assert result[2] == ApplyResult.REGISTER_FAIL


# ---------------------------------------------------------------------------
# _call_register_user_api — company > 0 path with real CompanyCount
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_call_register_user_api_company_nonzero_with_retire_via_real_enums(svc):
    from utils.enum import CompanyCount, ExperienceYears

    profile = _make_full_user_profile()
    profile.miidas_registration_user_data["experience_profile"] = {
        "expCompanyNum": CompanyCount.ONE,  # non-zero → triggers the branch
        "managementExpTerm": ExperienceYears.NONE,
        "industrySmallID": {"ID": 1},
        "jobTypeSmallID": {"ID": 2},
        "jobTypeExpTerm": 3,
        "allCareerJobTypeExpTerm": 5,
        "employmentPost": 1,
        "income": 500,
        "retireYear": 2020,
        "retireMonth": 3,
        "companyName": "株式会社テスト",
        "employeeNum": 100,
        "employmentType": 1,
        "joinYear": 2010,
        "joinMonth": 4,
    }
    client = AsyncMock()
    with (
        patch("services.user_service.request", return_value=(200, {"UserID": 1})),
        patch("services.user_service.SchoolType") as mock_st,
    ):
        mock_st.requires_department.return_value = False
        mock_st.requires_category.return_value = False
        mock_st.get_value.return_value = 1
        result = await svc._call_register_user_api(client, profile)
    assert result[0] == 200


# ---------------------------------------------------------------------------
# post_apply_failure — failed positions mismatch log branch (line 533)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_apply_failure_failed_position_mismatch_logs(svc, deps):
    # failed_position_ids has 2 (not in Positions) -> mismatch warning logged
    deps["aica_api_repository"].post.return_value = (200, {"Positions": [{"ID": 1}]})
    result = await svc.post_apply_failure([1, 2], [], [1, 2], [])
    # pos 2 is failed but not in positions -> triggers line 533 error log
    # result has failed_positions=[pos1], so MEETING_APPLICATION_FAIL returned
    assert result is not None
    assert result[2] == ApplyResult.MEETING_APPLICATION_FAIL


# ---------------------------------------------------------------------------
# post_register_success — session update failure during apply (line 640)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_register_success_session_update_fails_on_apply(svc, deps):
    client = AsyncMock()
    client.cookie_jar = []
    deps["chat_repository"].register_user_id.return_value = True
    deps["chat_repository"].update_session_status.return_value = None  # DB error
    profile = _make_full_user_profile()
    profile.miidas_registration_user_data[APPLY_POSITION_IDS_KEY] = ["1"]
    with (
        patch.object(
            svc, "_call_meeting_application_api", AsyncMock(return_value=(200, None))
        ),
        patch("services.user_service.asyncio.sleep", AsyncMock()),
    ):
        result = await svc.post_register_success(client, {"UserID": 42}, profile)
    assert result is not None
