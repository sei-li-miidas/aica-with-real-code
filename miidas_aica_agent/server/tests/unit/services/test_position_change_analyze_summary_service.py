import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.position_change_analyze_summary_service import PositionChangeAnalyzeSummaryService


MODEL_LIST = [
    {
        "model": "gpt-4.1-2025-04-14",
        "use_for": ["position_change_analyze_summary"],
        "model_settings": {"temperature": 1.0},
    }
]


class TestPositionChangeAnalyzeSummaryService:
    def test_init_raises_if_no_model(self):
        with pytest.raises(ValueError, match="position_change_analyze_summary"):
            PositionChangeAnalyzeSummaryService([{"model": "x", "use_for": ["other"]}])

    @pytest.mark.asyncio
    async def test_generate_summary_returns_dict(self):
        expected = {
            "summary": "転職軸です",
            "explanation": "AIの視点です",
            "keywords": ["フルリモート", "フレックス"],
        }
        mock_response = MagicMock()
        mock_response.output_text = json.dumps(expected)

        mock_client = MagicMock()
        mock_client.responses = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_response)

        with patch(
            "services.position_change_analyze_summary_service.AsyncOpenAI",
            return_value=mock_client,
        ):
            svc = PositionChangeAnalyzeSummaryService(MODEL_LIST)
            result = await svc.generate_summary("給与に不満があります")

        assert result == expected
        mock_client.responses.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_summary_with_curly_braces_in_input(self):
        expected = {
            "summary": "転職軸です",
            "explanation": "AIの視点です",
            "keywords": ["フルリモート", "フレックス"],
        }
        mock_response = MagicMock()
        mock_response.output_text = json.dumps(expected)

        mock_client = MagicMock()
        mock_client.responses = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_response)

        with patch(
            "services.position_change_analyze_summary_service.AsyncOpenAI",
            return_value=mock_client,
        ):
            svc = PositionChangeAnalyzeSummaryService(MODEL_LIST)
            result = await svc.generate_summary("給与{UP}を望む")

        assert result == expected

    @pytest.mark.asyncio
    async def test_generate_summary_raises_on_empty_response(self):
        mock_response = MagicMock()
        mock_response.output_text = ""

        mock_client = MagicMock()
        mock_client.responses = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_response)

        with patch(
            "services.position_change_analyze_summary_service.AsyncOpenAI",
            return_value=mock_client,
        ):
            svc = PositionChangeAnalyzeSummaryService(MODEL_LIST)
            with pytest.raises(RuntimeError, match="空"):
                await svc.generate_summary("テスト")

    @pytest.mark.asyncio
    async def test_generate_summary_raises_on_api_error(self):
        mock_client = MagicMock()
        mock_client.responses = MagicMock()
        mock_client.responses.create = AsyncMock(side_effect=RuntimeError("API error"))

        with patch(
            "services.position_change_analyze_summary_service.AsyncOpenAI",
            return_value=mock_client,
        ):
            svc = PositionChangeAnalyzeSummaryService(MODEL_LIST)
            with pytest.raises(RuntimeError, match="API error"):
                await svc.generate_summary("テスト")
