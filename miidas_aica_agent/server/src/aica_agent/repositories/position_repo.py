import copy
import logging
from typing import Any

from utils.const import LOGGER_PREFIX
from utils.crypt import encrypt
from utils.enum import EncryptKeyType
from utils.cache_utils import CacheUtil


class PositionRepository:
    """
    セッション毎にポジション関連情報のキャッシュ
    """

    def __init__(
        self,
        cache_util: CacheUtil,
    ):
        """
        下記のポジション情報キャッシュ初期化
        ・暗号化・復号化のキー（セッション毎異なる）
        ・ポジション検索結果
        ・ポジション詳細表示に関連する情報
            ・ポジション詳細
            ・会社詳細
            ・業界詳細
        ・ユーザー検索条件
        """
        self._logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self._cache = cache_util

    def save_search_result_position_ids(
        self,
        search_key: str,
        position_ids: list[int],
    ) -> int:
        """
        ポジション検索結果IDをキャッシュする

        Args:
            search_key: 検索キー
            position_ids: 検索結果のポジションIDリスト

        Returns:
            ポジション検索結果数
        """
        if not position_ids:
            return 0

        unique_position_ids = list(dict.fromkeys(position_ids))

        cache_key = CacheUtil.build_cache_key_with_session_id(
            "position_search_result_ids", search_key
        )
        self._cache.save(cache_key, unique_position_ids)

        return len(unique_position_ids)

    def get_cached_position_search_result(
        self,
        tool_call_id: str,
    ) -> list[int]:
        """
        キャッシュからポジション検索結果を取得

        Args:
            tool_call_id: ツールコールID

        Returns:
            ポジション検索結果
        """
        cache_key = CacheUtil.build_cache_key_with_session_id(
            "position_search_result_ids", tool_call_id
        )
        return self._cache.get_cached_list(cache_key)

    def remove_search_result_positions_ids(
        self,
        search_key: str,
        position_ids: list[int],
    ) -> int:
        """
        ポジション検索結果IDを削除

        Args:
            search_key: 検索キー
            position_ids: 削除するポジションIDリスト
        """
        cache_key = CacheUtil.build_cache_key_with_session_id(
            "position_search_result_ids", search_key
        )
        position_search_result = self._cache.get(cache_key)
        if position_search_result:
            position_search_result = [
                pid for pid in position_search_result if pid not in position_ids
            ]
            if position_search_result:
                self._cache.save(cache_key, position_search_result)
            else:
                self._cache.delete(cache_key)

        return len(position_search_result) if position_search_result else 0

    def process_and_cache_positions(
        self,
        positions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        ポジション検索結果をキャッシュする

        Args:
            positions: 検索結果

        Returns:
            処理後のポジションリスト
        """
        if not positions:
            return []

        for position in positions:
            real_id = str(position["ID"])
            try:
                position["ID"] = encrypt(EncryptKeyType.POSITION, real_id)
            except Exception:
                self._logger.exception("ポジションID暗号化失敗 %s", real_id)
                return []

        return positions

    def save_position_detail(
        self,
        position_id: str,
        position_detail: dict,
    ):
        """
        ポジション詳細APIレスポンスをキャッシュする

        Args:
            position_id: ポジションID
            position_detail: ポジション詳細APIレスポンス
        """
        cache_key = CacheUtil.build_cache_key_without_session_id(
            "position_detail", position_id
        )
        self._cache.save(cache_key, position_detail)

    def get_position_detail(
        self,
        position_id: str,
    ) -> dict | None:
        """
        メモリキャッシュからポジション詳細を取得

        Args:
            position_id: ポジションID

        Returns:
            キャッシュされたポジション詳細 or None
        """
        cache_key = CacheUtil.build_cache_key_without_session_id(
            "position_detail", position_id
        )
        position_detail = self._cache.get_cached_dict(cache_key)
        return position_detail

    def save_company_detail(
        self,
        position_id: str,
        company_detail: dict,
    ):
        """
        会社詳細APIレスポンスをキャッシュする

        Args:
            position_id: ポジションID
            company_detail: 会社詳細APIレスポンス
        """
        cache_key = CacheUtil.build_cache_key_without_session_id(
            "company_detail", position_id
        )
        self._cache.save(cache_key, company_detail)

    def get_company_detail(
        self,
        position_id: str,
    ) -> dict | None:
        """
        メモリキャッシュから会社詳細を取得

        Args:
            position_id: ポジションID

        Returns:
            キャッシュされた会社詳細 or None
        """
        cache_key = CacheUtil.build_cache_key_without_session_id(
            "company_detail", position_id
        )
        company_detail = self._cache.get_cached_dict(cache_key)
        return company_detail

    def save_business_detail(
        self,
        position_id: str,
        business_detail: dict,
    ):
        """
        業界詳細APIレスポンスをキャッシュする

        Args:
            position_id: ポジションID
            business_detail: 業界詳細APIレスポンス
        """
        cache_key = CacheUtil.build_cache_key_without_session_id(
            "business_detail", position_id
        )
        self._cache.save(cache_key, business_detail)

    def get_business_detail(
        self,
        position_id: str,
    ) -> dict | None:
        """
        メモリキャッシュから業界詳細を取得

        Args:
            position_id: ポジションID

        Returns:
            キャッシュされた業界詳細 or None
        """
        cache_key = CacheUtil.build_cache_key_without_session_id(
            "business_detail", position_id
        )
        business_detail = self._cache.get_cached_dict(cache_key)
        return business_detail

    def save_position_recommendations(
        self,
        recommendation_themes: list[str],
    ) -> dict[str, str]:
        """
        おすすめのリンクマッピング作成

        Args:
            recommendation_themes: おすすめパスリスト

        Returns:
            レコメンドリンクマッピング
        """
        return {
            theme: encrypt(EncryptKeyType.POSITION, theme)
            for theme in recommendation_themes
        }

    def process_position_search_result(
        self,
        tool_call_id: str,
        search_result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        ポジション検索結果処理

        Args:
            search_result: ポジション検索結果

        Returns:
            処理後のポジション検索結果
        """
        search_key = tool_call_id
        count = self.save_search_result_position_ids(
            search_key,
            search_result.get("AllPositionIds"),
        )

        position_summaries = self.process_and_cache_positions(
            search_result.get("Positions"),
        )

        recommendations = search_result.get("Recommendations", [])
        if recommendations:
            theme_mapping = self.save_position_recommendations(
                [rec["Theme"] for rec in recommendations],
            )
            for rec in recommendations:
                rec["Theme"] = theme_mapping.get(rec.get("Theme"))

        return {
            "SearchKey": search_key,
            "TotalPositionCount": count,
            "Positions": position_summaries,
            "Recommendations": recommendations,
            "SearchFilters": search_result.get("SearchFilters"),
            "JobtypeNamesWithSameSearchFilters": search_result.get(
                "JobtypeNamesWithSameSearchFilters"
            ),
        }
