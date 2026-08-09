from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from datetime import date
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
import statistics
from typing import Callable
from utils.enum import RateLimitScope
from utils.const import LOGGER_PREFIX
from utils.cache_utils import CacheUtil


class RateLimitArchiveRepository(ABC):
    @abstractmethod
    def aggregate_to_stats(
        self,
        target_date: date,
        action_type: str,
        scope: str,
        hours: int,
        limit: int,
    ) -> None:
        """指定されたルールのデータを集計し、集計テーブルへ登録する"""
        pass

    @abstractmethod
    def delete_old_records(
        self, target_date: date, all_rules: list[tuple[str, str, int, int]]
    ) -> int:
        """指定された日付のデータを削除し、削除件数を返す"""
        pass


class RedisRateLimitArchiveRepository(RateLimitArchiveRepository):
    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        cache_util: CacheUtil,
    ) -> None:
        self._session_factory = session_factory
        self._cache_util = cache_util
        self._logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )

    def _generate_time_keys(self, target_date: date, hours: int) -> list[str]:
        """指定された日付とwindow_hoursに基づいてtime_keyのリストを生成する"""
        if hours == 1:
            # 1時間ごとのキーを生成 (YYYYMMDDHH)
            return [f"{target_date.strftime('%Y%m%d')}{hour:02d}" for hour in range(24)]
        elif hours == 24:
            # 1日単位のキーを生成 (YYYYMMDD)
            return [target_date.strftime("%Y%m%d")]
        else:
            self._logger.error(
                "Unsupported window_hours for time_key generation: %s.", hours
            )
            return []

    def aggregate_to_stats(
        self, target_date: date, action_type: str, scope: str, hours: int, limit: int
    ) -> None:
        stats_to_insert = []
        time_keys_to_check = self._generate_time_keys(target_date, hours)

        for time_key in time_keys_to_check:
            key = f"{action_type}:{scope}:{hours}h:{time_key}"

            counts: list[int] = []
            if scope == RateLimitScope.GUEST:
                # String 型のデータを取得
                value = self._cache_util.get(key)
                if value:
                    try:
                        counts.append(int(value))
                    except (ValueError, TypeError):
                        self._logger.error(
                            "Could not parse value for key %s: %s", key, value
                        )
            elif scope in [RateLimitScope.SESSION, RateLimitScope.IP]:
                # Hash 型のデータ（値のみ）を取得
                hash_values = self._cache_util.get_hash_values(key)
                if hash_values:
                    try:
                        counts = [int(v) for v in hash_values]
                    except (ValueError, TypeError):
                        self._logger.error(
                            "Could not parse some values in hash for key %s : %s",
                            key,
                            hash_values,
                        )
                        continue

            if not counts:
                continue

            self._logger.info(
                "Aggregating stats for key %s with counts: %s", key, counts
            )

            # 集計処理
            num_records = len(counts)
            total_count = sum(counts)
            avg_count = statistics.mean(counts)
            max_count = max(counts)
            p50 = statistics.median(counts)
            p95 = statistics.quantiles(counts, n=100, method="inclusive")[94]
            p99 = statistics.quantiles(counts, n=100, method="inclusive")[98]
            exceeded_count = sum(1 for c in counts if c > limit)

            stats_to_insert.append(
                {
                    "target_date": target_date,
                    "action_type": action_type,
                    "scope": scope,
                    "window_size": f"{hours}h",
                    "time_key": time_key,
                    "record_count": num_records,
                    "total_count": total_count,
                    "avg_count": avg_count,
                    "max_count": max_count,
                    "p50_count": p50,
                    "p95_count": p95,
                    "p99_count": p99,
                    "exceeded_count": exceeded_count,
                    "threshold_value": limit,
                }
            )

        if not stats_to_insert:
            return

        # 集計結果をDBに一括登録
        with self._session_factory() as session:
            sql = text("""
                INSERT INTO rate_limit_stats (
                    aggregation_date, action_type, scope, window_size, time_key,
                    record_count, total_count, avg_count, max_count,
                    p50_count, p95_count, p99_count,
                    exceeded_count, "threshold_value"
                ) VALUES (
                    :target_date, :action_type, :scope, :window_size, :time_key,
                    :record_count, :total_count, :avg_count, :max_count,
                    :p50_count, :p95_count, :p99_count,
                    :exceeded_count, :threshold_value
                )
                ON CONFLICT (aggregation_date, action_type, scope, window_size, time_key) DO NOTHING;
            """)
            session.execute(sql, stats_to_insert)
            session.commit()

    def delete_old_records(
        self, target_date: date, all_rules: list[tuple[str, str, int, int]]
    ) -> int:
        keys_to_delete = []

        for action_type, scope, hours, _ in all_rules:
            time_keys = self._generate_time_keys(target_date, hours)
            for time_key in time_keys:
                key = f"{action_type}:{scope}:{hours}h:{time_key}"
                keys_to_delete.append(key)

        # 生成したキーをチャンクに分けて削除
        deleted_count = 0
        chunk_size = 500
        if keys_to_delete:
            for i in range(0, len(keys_to_delete), chunk_size):
                chunk = keys_to_delete[i : i + chunk_size]
                deleted_count += self._cache_util.delete(*chunk)

        return deleted_count
