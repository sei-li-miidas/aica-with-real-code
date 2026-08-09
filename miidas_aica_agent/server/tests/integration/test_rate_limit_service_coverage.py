"""
Integration tests for RateLimitService — targeting 100% branch coverage.

Tests call the real service with mocked repositories, exercising all branches.
"""

from unittest.mock import Mock

import pytest

from domain.entities.rate_limit_rule import RateLimitRule
from repositories.rate_limit_repo import BaseRateLimitRepository
from services.rate_limit_service import RateLimitService

pytestmark = pytest.mark.pre_extraction_parity


def _make_svc(rate_limit: dict) -> RateLimitService:
    return RateLimitService(
        rate_limit_repository=Mock(spec=BaseRateLimitRepository),
        rate_limit=rate_limit,
    )


def _empty_config() -> dict:
    return {
        "chat_request": {},
        "position_detail": {},
        "position_search": {},
        "load_more_positions": {},
    }


def _rule(limit: int = 100, window_hours: int = 1) -> dict:
    return {"window_hours": window_hours, "limit": limit}


# ── is_within_chat_request_limit ────────────────────────────────────────────


def test_chat_request_no_rules_returns_true():
    svc = _make_svc(_empty_config())
    assert svc.is_within_chat_request_limit("sess-1", "1.2.3.4") is True
    # try_increment must NOT be called when checks list is empty
    svc._rate_limit_repository.try_increment.assert_not_called()


def test_chat_request_session_rule_delegates_to_repo():
    config = _empty_config()
    config["chat_request"] = {"session": [_rule()]}
    svc = _make_svc(config)
    svc._rate_limit_repository.try_increment.return_value = True
    result = svc.is_within_chat_request_limit("sess-1", "1.2.3.4")
    assert result is True
    svc._rate_limit_repository.try_increment.assert_called_once()


def test_chat_request_ip_rule_delegates_to_repo():
    config = _empty_config()
    config["chat_request"] = {"ip": [_rule()]}
    svc = _make_svc(config)
    svc._rate_limit_repository.try_increment.return_value = False
    result = svc.is_within_chat_request_limit("sess-1", "1.2.3.4")
    assert result is False


def test_chat_request_guest_rule_delegates_to_repo():
    config = _empty_config()
    config["chat_request"] = {"guest": [_rule()]}
    svc = _make_svc(config)
    svc._rate_limit_repository.try_increment.return_value = True
    result = svc.is_within_chat_request_limit("", "")
    assert result is True


def test_chat_request_multiple_scopes_combined():
    config = _empty_config()
    config["chat_request"] = {
        "session": [_rule(limit=10)],
        "ip": [_rule(limit=20)],
        "guest": [_rule(limit=50)],
    }
    svc = _make_svc(config)
    svc._rate_limit_repository.try_increment.return_value = True
    svc.is_within_chat_request_limit("sess-abc", "10.0.0.1")
    # All 3 rules should be merged into one checks list
    args = svc._rate_limit_repository.try_increment.call_args[0][0]
    assert len(args) == 3


def test_chat_request_empty_session_id_skips_session_rule():
    config = _empty_config()
    config["chat_request"] = {"session": [_rule()]}
    svc = _make_svc(config)
    # empty session_id → no checks → returns True without calling try_increment
    result = svc.is_within_chat_request_limit("", "10.0.0.1")
    assert result is True
    svc._rate_limit_repository.try_increment.assert_not_called()


def test_chat_request_empty_ip_skips_ip_rule():
    config = _empty_config()
    config["chat_request"] = {"ip": [_rule()]}
    svc = _make_svc(config)
    result = svc.is_within_chat_request_limit("sess-1", "")
    assert result is True
    svc._rate_limit_repository.try_increment.assert_not_called()


# ── is_within_position_detail_limit ─────────────────────────────────────────


def test_position_detail_no_rules_returns_true():
    svc = _make_svc(_empty_config())
    assert svc.is_within_position_detail_limit("sess-1", "1.2.3.4") is True


def test_position_detail_with_rule_delegates_to_repo():
    config = _empty_config()
    config["position_detail"] = {"session": [_rule()]}
    svc = _make_svc(config)
    svc._rate_limit_repository.try_increment.return_value = True
    assert svc.is_within_position_detail_limit("sess-x", "1.1.1.1") is True
    svc._rate_limit_repository.try_increment.assert_called_once()


def test_position_detail_exceeded_returns_false():
    config = _empty_config()
    config["position_detail"] = {"guest": [_rule(limit=0)]}
    svc = _make_svc(config)
    svc._rate_limit_repository.try_increment.return_value = False
    assert svc.is_within_position_detail_limit("s", "ip") is False


# ── is_within_position_search_limit ─────────────────────────────────────────


def test_position_search_no_rules_returns_true():
    svc = _make_svc(_empty_config())
    assert svc.is_within_position_search_limit("sess-1", "1.2.3.4") is True


def test_position_search_with_rule_delegates_to_repo():
    config = _empty_config()
    config["position_search"] = {"ip": [_rule()]}
    svc = _make_svc(config)
    svc._rate_limit_repository.try_increment.return_value = True
    assert svc.is_within_position_search_limit("s", "2.2.2.2") is True
    svc._rate_limit_repository.try_increment.assert_called_once()


def test_position_search_exceeded_returns_false():
    config = _empty_config()
    config["position_search"] = {"guest": [_rule()]}
    svc = _make_svc(config)
    svc._rate_limit_repository.try_increment.return_value = False
    assert svc.is_within_position_search_limit("s", "ip") is False


# ── is_within_load_more_positions_limit ─────────────────────────────────────


def test_load_more_no_rules_returns_true():
    svc = _make_svc(_empty_config())
    assert svc.is_within_load_more_positions_limit("sess-1", "1.2.3.4") is True


def test_load_more_with_rule_delegates_to_repo():
    config = _empty_config()
    config["load_more_positions"] = {"session": [_rule()]}
    svc = _make_svc(config)
    svc._rate_limit_repository.try_increment.return_value = True
    assert svc.is_within_load_more_positions_limit("s", "3.3.3.3") is True
    svc._rate_limit_repository.try_increment.assert_called_once()


def test_load_more_exceeded_returns_false():
    config = _empty_config()
    config["load_more_positions"] = {"guest": [_rule()]}
    svc = _make_svc(config)
    svc._rate_limit_repository.try_increment.return_value = False
    assert svc.is_within_load_more_positions_limit("s", "ip") is False
