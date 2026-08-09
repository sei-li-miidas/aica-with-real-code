from unittest.mock import Mock

import pytest

from repositories.rate_limit_repo import BaseRateLimitRepository
from services.rate_limit_service import RateLimitService

pytestmark = pytest.mark.pre_extraction_parity


def test_chat_request_no_checks_returns_true_without_try_increment():
    repo = Mock(spec=BaseRateLimitRepository)
    service = RateLimitService(
        repo,
        {
            "chat_request": {},
            "position_detail": {},
            "position_search": {},
            "load_more_positions": {},
        },
    )

    assert service.is_within_chat_request_limit("", "") is True
    repo.try_increment.assert_not_called()


def test_position_search_limit_uses_try_increment_when_rules_exist():
    repo = Mock(spec=BaseRateLimitRepository)
    repo.try_increment.return_value = True
    service = RateLimitService(
        repo,
        {
            "chat_request": {},
            "position_detail": {},
            "position_search": {
                "session": [{"window_hours": 1, "limit": 2}],
            },
            "load_more_positions": {},
        },
    )

    assert service.is_within_position_search_limit("sid", "") is True
    repo.try_increment.assert_called_once()


def test_load_more_positions_limit_uses_try_increment_when_rules_exist():
    repo = Mock(spec=BaseRateLimitRepository)
    repo.try_increment.return_value = False
    service = RateLimitService(
        repo,
        {
            "chat_request": {},
            "position_detail": {},
            "position_search": {},
            "load_more_positions": {
                "ip": [{"window_hours": 1, "limit": 3}],
            },
        },
    )

    assert service.is_within_load_more_positions_limit("", "127.0.0.1") is False
    repo.try_increment.assert_called_once()
