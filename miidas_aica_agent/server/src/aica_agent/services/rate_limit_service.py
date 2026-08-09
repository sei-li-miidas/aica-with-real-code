from services.base_service import BaseService
from pydantic import BaseModel
from repositories.rate_limit_repo import BaseRateLimitRepository
from utils.enum import RateLimitActionType, RateLimitScope
from domain.entities.rate_limit_rule import RateLimitRule


class ActionLimits(BaseModel):
    guest: list[RateLimitRule] = []
    session: list[RateLimitRule] = []
    ip: list[RateLimitRule] = []


class RateLimitConfig(BaseModel):
    chat_request: ActionLimits
    position_detail: ActionLimits
    position_search: ActionLimits
    load_more_positions: ActionLimits


class RateLimitService(BaseService):
    def __init__(
        self,
        rate_limit_repository: BaseRateLimitRepository,
        rate_limit: dict,
    ) -> None:
        super().__init__()

        self._rate_limit_repository = rate_limit_repository
        self._rate_limit = RateLimitConfig(**rate_limit)

    def _build_ordered_checks(
        self,
        action_type: RateLimitActionType,
        limits: ActionLimits,
        session_id: str,
        ip_address: str,
    ) -> list:
        """
        指定された機能の設定に基づき、チェックリストを生成する。
        狭いスコープ(Session) -> 中(IP) -> 広(Guest) の順序でルールを適用する。
        """
        checks = []

        def add_rules(
            scope: RateLimitScope, identifier: str | None, rules: list[RateLimitRule]
        ):
            for rule in rules:
                checks.append((action_type, scope, identifier, rule))

        # セッションID
        if session_id and limits.session:
            add_rules(RateLimitScope.SESSION, session_id, limits.session)

        # IPアドレス
        if ip_address and limits.ip:
            add_rules(RateLimitScope.IP, ip_address, limits.ip)

        # 非会員全体
        if limits.guest:
            add_rules(RateLimitScope.GUEST, None, limits.guest)

        return checks

    def is_within_chat_request_limit(self, session_id: str, ip_address: str) -> bool:
        """
        チャットリクエストのレート制限をチェックする。
        """
        checks = self._build_ordered_checks(
            RateLimitActionType.CHAT_REQUEST,
            self._rate_limit.chat_request,
            session_id,
            ip_address,
        )

        if not checks:
            return True

        return self._rate_limit_repository.try_increment(checks)

    def is_within_position_detail_limit(self, session_id: str, ip_address: str) -> bool:
        """
        求人詳細閲覧のレート制限をチェックする。
        """
        checks = self._build_ordered_checks(
            RateLimitActionType.POSITION_DETAIL,
            self._rate_limit.position_detail,
            session_id,
            ip_address,
        )

        if not checks:
            return True

        return self._rate_limit_repository.try_increment(checks)

    def is_within_position_search_limit(self, session_id: str, ip_address: str) -> bool:
        """
        求人検索のレート制限をチェックする。
        """
        checks = self._build_ordered_checks(
            RateLimitActionType.POSITION_SEARCH,
            self._rate_limit.position_search,
            session_id,
            ip_address,
        )

        if not checks:
            return True

        return self._rate_limit_repository.try_increment(checks)

    def is_within_load_more_positions_limit(
        self, session_id: str, ip_address: str
    ) -> bool:
        """
        求人をもっと見るのレート制限をチェックする。
        """
        checks = self._build_ordered_checks(
            RateLimitActionType.LOAD_MORE_POSITIONS,
            self._rate_limit.load_more_positions,
            session_id,
            ip_address,
        )

        if not checks:
            return True

        return self._rate_limit_repository.try_increment(checks)
