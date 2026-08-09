from datetime import date
import logging
from pydantic import BaseModel
from repositories.rate_limit_archive_repo import RateLimitArchiveRepository
from utils.const import LOGGER_PREFIX
from utils.enum import RateLimitScope


class RateLimitRule(BaseModel):
    window_hours: int
    limit: int


class ActionLimits(BaseModel):
    session: list[RateLimitRule] = []
    ip: list[RateLimitRule] = []
    guest: list[RateLimitRule] = []


class RateLimitConfig(BaseModel):
    chat_request: ActionLimits
    position_detail: ActionLimits
    position_search: ActionLimits
    load_more_positions: ActionLimits


class AggregateAndDeleteRateLimits:
    """日次で、前日分のレート制限データを集計し削除する"""

    def __init__(
        self,
        rate_limit_archive_repository: RateLimitArchiveRepository,
        rate_limit: dict,
    ) -> None:
        self._rate_limit_archive_repository = rate_limit_archive_repository
        self._rate_limit = RateLimitConfig(**rate_limit)
        self._logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )

    def _extract_rules(self, rate_limit: RateLimitConfig):
        """レート制限の設定値から、全てのルールを抽出する"""
        for action_type, action_limits in rate_limit:
            if not action_limits:
                continue

            scope_map = [
                (RateLimitScope.SESSION, action_limits.session),
                (RateLimitScope.IP, action_limits.ip),
                (RateLimitScope.GUEST, action_limits.guest),
            ]

            for scope, rules in scope_map:
                for rule in rules:
                    yield (action_type, scope, rule.window_hours, rule.limit)

    def execute(self, target_date: date):
        try:
            all_rules = list(self._extract_rules(self._rate_limit))

            self._logger.info(
                "--- Start Aggregate and Delete Process for %s ---", target_date
            )

            # レート制限ルールごとに集計を実行
            for action_type, scope, hours, limit in all_rules:
                self._logger.info(
                    "Aggregating stats for %s, %s, %sh window",
                    action_type,
                    scope,
                    hours,
                )
                self._rate_limit_archive_repository.aggregate_to_stats(
                    target_date,
                    action_type,
                    scope,
                    hours,
                    limit,
                )

            self._logger.info("Deleting old records for %s", target_date)
            deleted_count = self._rate_limit_archive_repository.delete_old_records(
                target_date, all_rules
            )

            self._logger.info(
                "Process completed. Deleted records from Valkey: %s", deleted_count
            )

        except Exception:
            self._logger.exception("Batch failed")
            raise
