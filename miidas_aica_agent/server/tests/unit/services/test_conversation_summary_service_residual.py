import pytest

from services.conversation_summary_service import ConversationSummaryService

pytestmark = pytest.mark.pre_extraction_parity


@pytest.fixture
def svc():
    service = object.__new__(ConversationSummaryService)
    return service


def test_init_raises_when_model_key_missing():
    with pytest.raises(ValueError, match="Summary model name is not configured"):
        ConversationSummaryService(
            model_list=[{"use_for": ["summary"], "model_settings": {}}]
        )


def test_init_warns_when_multiple_summary_models(caplog):
    with pytest.raises(ValueError):
        ConversationSummaryService(
            model_list=[
                {"use_for": ["summary"], "model_settings": {}},
                {"use_for": ["summary"], "model_settings": {}},
            ]
        )
    assert "複数の会話要約モデルが定義されています" in caplog.text


def test_is_retryable_summary_error_by_status_code_429(svc):
    err = Exception("x")
    setattr(err, "status_code", 429)
    assert svc._is_retryable_summary_error(err) is True


def test_is_retryable_summary_error_by_status_code_5xx(svc):
    err = Exception("x")
    setattr(err, "status_code", 503)
    assert svc._is_retryable_summary_error(err) is True


def test_format_summary_tool_response_for_non_position_tool_returns_raw(svc):
    raw = "raw-response"
    assert svc._format_summary_tool_response("non_position_tool", raw) == raw


def test_format_summary_tool_response_returns_fake_when_count_missing(svc):
    result = svc._format_summary_tool_response("search_job_postings", "not-json")
    assert "検索結果" in result


def test_extract_position_count_returns_none_for_non_list_json(svc):
    assert svc._extract_position_count_from_tool_output('{"x": 1}') is None


def test_extract_position_count_returns_none_for_non_dict_first_item(svc):
    assert svc._extract_position_count_from_tool_output('["x"]') is None


def test_extract_position_count_returns_none_for_non_string_text(svc):
    assert svc._extract_position_count_from_tool_output('[{"text": 123}]') is None


def test_extract_position_count_returns_none_for_non_dict_inner_json(svc):
    assert svc._extract_position_count_from_tool_output('[{"text": "[1,2]"}]') is None


def test_extract_position_count_returns_none_when_all_position_ids_not_list(svc):
    assert (
        svc._extract_position_count_from_tool_output(
            '[{"text": "{\\"AllPositionIds\\": 1}"}]'
        )
        is None
    )


def test_extract_position_count_returns_none_on_json_type_error(svc):
    assert svc._extract_position_count_from_tool_output(None) is None
