import pytest
from unittest.mock import Mock
from repositories.rate_limit_repo import BaseRateLimitRepository

pytestmark = pytest.mark.pre_extraction_parity
from services.rate_limit_service import RateLimitService, RateLimitConfig
from domain.entities.rate_limit_rule import RateLimitRule
from utils.enum import RateLimitActionType, RateLimitScope

# テスト用のRateLimitConfig
TEST_CONFIG: RateLimitConfig = {
    "chat_request": {
        "session": [{"window_hours": 24, "limit": 100}],
        "ip": [{"window_hours": 1, "limit": 20}],
        "guest": [{"window_hours": 1, "limit": 5}],
    },
    "position_detail": {"ip": [{"window_hours": 24, "limit": 500}]},
    "position_search": {},
    "load_more_positions": {},
}


@pytest.fixture
def mock_rate_limit_repo():
    """
    BaseRateLimitRepositoryのモック
    """
    return Mock(spec=BaseRateLimitRepository)


@pytest.fixture
def rate_limit_service(mock_rate_limit_repo):
    """
    RateLimitServiceのインスタンスを生成
    """
    return RateLimitService(
        rate_limit_repository=mock_rate_limit_repo, rate_limit=TEST_CONFIG
    )


class TestRateLimitService:
    def test_is_within_chat_request_limit_builds_correct_checks(
        self, rate_limit_service, mock_rate_limit_repo
    ):
        # Setup
        session_id = "test_session"
        ip_address = "127.0.0.1"
        mock_rate_limit_repo.try_increment.return_value = True

        # Execute
        result = rate_limit_service.is_within_chat_request_limit(session_id, ip_address)

        # Verify
        assert result is True

        # try_incrementに渡された引数を取得
        args, _ = mock_rate_limit_repo.try_increment.call_args
        checks = args[0]

        # checksの内容が正しいか検証
        assert len(checks) == 3

        # 1. session
        action_type, scope, identifier, rule = checks[0]
        assert action_type == RateLimitActionType.CHAT_REQUEST
        assert scope == RateLimitScope.SESSION
        assert identifier == session_id
        assert rule == RateLimitRule(window_hours=24, limit=100)

        # 2. ip
        action_type, scope, identifier, rule = checks[1]
        assert scope == RateLimitScope.IP
        assert identifier == ip_address
        assert rule == RateLimitRule(window_hours=1, limit=20)

        # 3. guest
        action_type, scope, identifier, rule = checks[2]
        assert scope == RateLimitScope.GUEST
        assert identifier is None
        assert rule == RateLimitRule(window_hours=1, limit=5)

    def test_is_within_limit_no_rules(self, mock_rate_limit_repo):
        # ルールが存在しない場合
        empty_config = {
            "chat_request": {},
            "position_detail": {},
            "position_search": {},
            "load_more_positions": {},
        }
        service = RateLimitService(mock_rate_limit_repo, empty_config)

        result = service.is_within_position_search_limit("sid", "ip")

        assert result is True
        mock_rate_limit_repo.try_increment.assert_not_called()  # try_incrementが呼ばれない

    def test_is_within_limit_exceeded(self, rate_limit_service, mock_rate_limit_repo):
        # 制限超過の場合
        mock_rate_limit_repo.try_increment.return_value = False

        result = rate_limit_service.is_within_chat_request_limit("sid", "ip")

        assert result is False
        mock_rate_limit_repo.try_increment.assert_called_once()

    def test_is_within_position_detail_limit_with_rules(
        self, rate_limit_service, mock_rate_limit_repo
    ):
        mock_rate_limit_repo.try_increment.return_value = True
        result = rate_limit_service.is_within_position_detail_limit("sid", "ip")
        assert result is True
        mock_rate_limit_repo.try_increment.assert_called()

    def test_is_within_position_detail_limit_no_rules(self, mock_rate_limit_repo):
        empty_config = {
            "chat_request": {},
            "position_detail": {},
            "position_search": {},
            "load_more_positions": {},
        }
        service = RateLimitService(mock_rate_limit_repo, empty_config)
        result = service.is_within_position_detail_limit("sid", "ip")
        assert result is True
        mock_rate_limit_repo.try_increment.assert_not_called()

    def test_is_within_position_search_limit_with_rules(
        self, rate_limit_service, mock_rate_limit_repo
    ):
        mock_rate_limit_repo.try_increment.return_value = True
        result = rate_limit_service.is_within_position_search_limit("sid", "ip")
        assert result is True

    def test_is_within_load_more_positions_limit_with_rules(
        self, rate_limit_service, mock_rate_limit_repo
    ):
        mock_rate_limit_repo.try_increment.return_value = True
        result = rate_limit_service.is_within_load_more_positions_limit("sid", "ip")
        assert result is True

    def test_is_within_load_more_positions_limit_no_rules(self, mock_rate_limit_repo):
        empty_config = {
            "chat_request": {},
            "position_detail": {},
            "position_search": {},
            "load_more_positions": {},
        }
        service = RateLimitService(mock_rate_limit_repo, empty_config)
        result = service.is_within_load_more_positions_limit("sid", "ip")
        assert result is True
