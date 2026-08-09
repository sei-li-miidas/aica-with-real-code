import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import endpoints


@pytest.mark.asyncio
async def test_health_returns_ok():
    result = await endpoints.health()
    assert result == {"status": "OK"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exist", "expected_status_code"),
    [
        (True, 200),
        (False, 404),
    ],
)
async def test_has_position_chat_returns_status_by_existence(
    exist, expected_status_code
):
    chat_svc = AsyncMock()
    chat_svc.check_if_previous_chat_histories_exist.return_value = exist

    resp = await endpoints.has_position_chat(position_id="encrypted", chat_svc=chat_svc)

    assert resp.status_code == expected_status_code
    assert json.loads(resp.body) == {}


@pytest.mark.asyncio
async def test_has_position_chat_returns_500_on_exception():
    chat_svc = AsyncMock()
    chat_svc.check_if_previous_chat_histories_exist.side_effect = RuntimeError("boom")

    resp = await endpoints.has_position_chat(position_id="encrypted", chat_svc=chat_svc)

    assert resp.status_code == 500
    assert json.loads(resp.body) == {}


@pytest.mark.asyncio
async def test_load_previous_chat_histories_returns_payload():
    chat_svc = AsyncMock()
    chat_svc.load_previous_chat_histories.return_value = (
        [{"Role": "assistant", "MessageID": "a1"}],
        False,
    )

    resp = await endpoints.load_previous_chat_histories(
        position_id=None,
        before_id="m1",
        limit=3,
        chat_svc=chat_svc,
    )

    assert resp.status_code == 200
    assert json.loads(resp.body) == {
        "PreviousChatHistories": [{"Role": "assistant", "MessageID": "a1"}],
        "NoMoreUserMessageLeft": False,
    }


@pytest.mark.asyncio
async def test_load_previous_chat_histories_returns_500_on_exception():
    chat_svc = AsyncMock()
    chat_svc.load_previous_chat_histories.side_effect = RuntimeError("boom")

    resp = await endpoints.load_previous_chat_histories(
        position_id=None,
        before_id="m1",
        limit=3,
        chat_svc=chat_svc,
    )

    assert resp.status_code == 500
    assert json.loads(resp.body) == {}


# ============================================================================
# 新規テスト: Feature #78051 - 職種別ポジション検索エンドポイント
# ============================================================================


@pytest.mark.asyncio
async def test_current_search_filter_returns_search_conditions():
    """
    最新ポジション検索条件取得エンドポイントが検索条件を返すことを確認する
    """
    position_svc = Mock()
    position_svc.current_search_filter = AsyncMock(
        return_value={
            "SearchFilters": {"LocationType": "OFFICE", "SalaryMin": 5000000},
            "JobtypeNamesWithSameSearchFilters": ["IT", "Finance"],
        }
    )

    result = await endpoints.current_search_filter(position_svc=position_svc)

    assert result == {
        "SearchFilters": {"LocationType": "OFFICE", "SalaryMin": 5000000},
        "JobtypeNamesWithSameSearchFilters": ["IT", "Finance"],
    }


@pytest.mark.asyncio
async def test_current_search_filter_returns_empty_when_no_filters():
    """
    検索条件がない場合は空または None を返すことを確認する
    """
    position_svc = Mock()
    position_svc.current_search_filter = AsyncMock(return_value=None)

    result = await endpoints.current_search_filter(position_svc=position_svc)

    assert result is None


@pytest.mark.asyncio
async def test_jobtype_other_filter_with_single_jobtype():
    """
    単一職種でのジョブタイプ別フィルタ取得エンドポイントをテストする
    """
    position_svc = Mock()
    position_svc.jobtype_other_filter = AsyncMock(
        return_value={
            "JobtypeName": "IT",
            "SearchFilters": {"SalaryMin": 5000000, "LocationType": "OFFICE"},
        }
    )

    result = await endpoints.jobtype_other_filter(
        jobtype_name="IT", position_svc=position_svc
    )

    position_svc.jobtype_other_filter.assert_called_once_with("IT")
    assert result["JobtypeName"] == "IT"
    assert result["SearchFilters"]["SalaryMin"] == 5000000


@pytest.mark.asyncio
async def test_jobtype_other_filter_with_multiple_search_parameters():
    """
    複数の検索パラメータでジョブタイプ別フィルタ取得をテストする
    """
    position_svc = Mock()
    position_svc.jobtype_other_filter = AsyncMock(
        return_value={
            "JobtypeName": "Finance",
            "SearchFilters": {
                "SalaryMin": 6000000,
                "SalaryMax": 8000000,
                "LocationType": "REMOTE",
                "Experience": "3-5 years",
            },
        }
    )

    result = await endpoints.jobtype_other_filter(
        jobtype_name="Finance", position_svc=position_svc
    )

    position_svc.jobtype_other_filter.assert_called_once_with("Finance")
    assert result["JobtypeName"] == "Finance"
    assert result["SearchFilters"]["LocationType"] == "REMOTE"
    assert result["SearchFilters"]["Experience"] == "3-5 years"


@pytest.mark.asyncio
async def test_jobtype_other_filter_returns_empty_when_no_matching_jobtype():
    """
    マッチするジョブタイプがない場合は空結果を返すことを確認する
    """
    position_svc = Mock()
    position_svc.jobtype_other_filter = AsyncMock(return_value={})

    result = await endpoints.jobtype_other_filter(
        jobtype_name="NonExistent", position_svc=position_svc
    )

    position_svc.jobtype_other_filter.assert_called_once_with("NonExistent")
    assert result == {}


@pytest.mark.asyncio
async def test_jobtype_specific_position_search_returns_positions():
    """
    職種別ポジション検索エンドポイントが検索結果を返すことを確認する
    """
    position_svc = Mock()
    position_svc.jobtype_specific_position_search = AsyncMock(
        return_value={
            "SearchKey": "search-1",
            "TotalPositionCount": 25,
            "Positions": [
                {"PositionID": "enc-1", "Title": "Senior Engineer", "Salary": 7000000},
                {"PositionID": "enc-2", "Title": "Lead Developer", "Salary": 8000000},
            ],
            "SearchFilters": {"JobtypeNames": ["IT", "Engineering"]},
        }
    )

    request = {
        "JobtypeNames": ["IT", "Engineering"],
        "LocationType": "OFFICE",
    }
    result = await endpoints.jobtype_specific_position_search(
        json_request=request, position_svc=position_svc
    )

    position_svc.jobtype_specific_position_search.assert_called_once_with(request)
    assert result["TotalPositionCount"] == 25
    assert len(result["Positions"]) == 2
    assert result["Positions"][0]["Title"] == "Senior Engineer"


@pytest.mark.asyncio
async def test_jobtype_specific_position_search_with_multiple_jobtypes():
    """
    複数職種でのポジション検索をテストする
    """
    position_svc = Mock()
    position_svc.jobtype_specific_position_search = AsyncMock(
        return_value={
            "SearchKey": "search-2",
            "TotalPositionCount": 50,
            "Positions": [
                {"PositionID": "enc-3", "JobtypeName": "IT"},
                {"PositionID": "enc-4", "JobtypeName": "Finance"},
                {"PositionID": "enc-5", "JobtypeName": "Sales"},
            ],
            "SearchFilters": {"JobtypeNames": ["IT", "Finance", "Sales"]},
        }
    )

    request = {
        "JobtypeNames": ["IT", "Finance", "Sales"],
        "SalaryMin": 5000000,
    }
    result = await endpoints.jobtype_specific_position_search(
        json_request=request, position_svc=position_svc
    )

    assert result["TotalPositionCount"] == 50
    assert len(result["Positions"]) == 3
    assert "IT" in result["SearchFilters"]["JobtypeNames"]
    assert "Finance" in result["SearchFilters"]["JobtypeNames"]


@pytest.mark.asyncio
async def test_jobtype_specific_position_search_returns_empty_when_no_matches():
    """
    マッチするポジションがない場合は0件結果を返すことを確認する
    """
    position_svc = Mock()
    position_svc.jobtype_specific_position_search = AsyncMock(
        return_value={
            "SearchKey": "search-empty",
            "TotalPositionCount": 0,
            "Positions": [],
        }
    )

    request = {
        "JobtypeNames": ["NonExistent"],
        "SalaryMin": 10000000,  # 非常に高い給与条件
    }
    result = await endpoints.jobtype_specific_position_search(
        json_request=request, position_svc=position_svc
    )

    assert result["TotalPositionCount"] == 0
    assert result["Positions"] == []


@pytest.mark.asyncio
async def test_current_search_filter_handles_service_error():
    """
    サービス層でのエラーをハンドルすることを確認する
    """
    position_svc = Mock()
    position_svc.current_search_filter = AsyncMock(
        side_effect=RuntimeError("API error")
    )

    with pytest.raises(RuntimeError):
        await endpoints.current_search_filter(position_svc=position_svc)


@pytest.mark.asyncio
async def test_jobtype_other_filter_handles_service_error():
    """
    サービス層でのエラーをハンドルすることを確認する
    """
    position_svc = Mock()
    position_svc.jobtype_other_filter = AsyncMock(side_effect=RuntimeError("API error"))

    with pytest.raises(RuntimeError):
        await endpoints.jobtype_other_filter(
            jobtype_name="IT", position_svc=position_svc
        )

    position_svc.jobtype_other_filter.assert_called_once_with("IT")


@pytest.mark.asyncio
async def test_jobtype_specific_position_search_handles_service_error():
    """
    サービス層でのエラーをハンドルすることを確認する
    """
    position_svc = Mock()
    position_svc.jobtype_specific_position_search = AsyncMock(
        side_effect=RuntimeError("Search failed")
    )

    request = {"JobtypeNames": ["IT"]}
    with pytest.raises(RuntimeError):
        await endpoints.jobtype_specific_position_search(
            json_request=request, position_svc=position_svc
        )


@pytest.mark.asyncio
async def test_search_job_match_diagnosis_occupations_returns_occupations():
    """
    適職診断の職種検索エンドポイントが職種リストを返すことを確認する
    """
    workflow_svc = Mock()
    expected_results = [
        {"ID": "1", "職種名": "エンジニア", "職種説明": "開発を行います"},
        {"ID": "2", "職種名": "デザイナー", "職種説明": "設計を行います"},
    ]
    workflow_svc.search_job_match_diagnosis_occupations = AsyncMock(
        return_value=expected_results
    )

    request = SimpleNamespace(answers={"1": [1, 2, 3], "2": [4]})

    result = await endpoints.search_job_match_diagnosis_occupations(
        request=request, workflow_svc=workflow_svc
    )

    workflow_svc.search_job_match_diagnosis_occupations.assert_called_once_with(
        request.answers
    )
    assert result == expected_results


@pytest.mark.asyncio
async def test_search_job_match_diagnosis_occupations_returns_500_on_exception():
    """
    適職診断の職種検索エンドポイントが例外発生時に500エラーを返すことを確認する
    """
    workflow_svc = Mock()
    workflow_svc.search_job_match_diagnosis_occupations = AsyncMock(
        side_effect=RuntimeError("API failure")
    )

    request = SimpleNamespace(answers={"1": [1, 2, 3], "2": [4]})

    resp = await endpoints.search_job_match_diagnosis_occupations(
        request=request, workflow_svc=workflow_svc
    )

    assert resp.status_code == 500
    assert json.loads(resp.body) == []


@pytest.mark.asyncio
async def test_generate_position_change_analyze_summary_returns_summary():
    """
    転職理由診断の転職軸要約生成エンドポイントが要約dictを返すことを確認する
    """
    workflow_svc = Mock()
    expected_summary = {
        "summary": "転職軸まとめ",
        "explanation": "AIの視点まとめ",
        "keywords": ["フルリモート", "フレックス"],
    }
    workflow_svc.generate_position_change_analyze_summary = AsyncMock(
        return_value=expected_summary
    )

    request = SimpleNamespace(answers={"1": [{"value": 1}], "2": [{"value": 1}]})

    result = await endpoints.generate_position_change_analyze_summary(
        request=request, workflow_svc=workflow_svc
    )

    workflow_svc.generate_position_change_analyze_summary.assert_called_once_with(
        request.answers
    )
    assert result == expected_summary


@pytest.mark.asyncio
async def test_generate_position_change_analyze_summary_returns_500_on_exception():
    """
    転職理由診断の転職軸要約生成エンドポイントが例外発生時に500エラーを返すことを確認する
    """
    workflow_svc = Mock()
    workflow_svc.generate_position_change_analyze_summary = AsyncMock(
        side_effect=RuntimeError("LLM failure")
    )

    request = SimpleNamespace(answers={"1": [{"value": 1}]})

    resp = await endpoints.generate_position_change_analyze_summary(
        request=request, workflow_svc=workflow_svc
    )

    assert resp.status_code == 500
    assert json.loads(resp.body) == {}


@pytest.mark.asyncio
async def test_generate_position_change_analyze_summary_returns_500_on_missing_step():
    """
    必須ステップ欠落時（ValueError）も他の例外と同様に500エラーになることを確認する
    """
    workflow_svc = Mock()
    workflow_svc.generate_position_change_analyze_summary = AsyncMock(
        side_effect=ValueError("転職理由診断要約に必要なステップ 4 の回答がありません")
    )

    request = SimpleNamespace(answers={"1": [{"value": 1}]})

    resp = await endpoints.generate_position_change_analyze_summary(
        request=request, workflow_svc=workflow_svc
    )

    assert resp.status_code == 500
    assert json.loads(resp.body) == {}
