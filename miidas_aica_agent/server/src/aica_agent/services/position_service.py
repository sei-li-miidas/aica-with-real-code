import asyncio
import json
from typing import Any
import uuid
from repositories.action_log_repo import ActionLogRepository, ActionLogType
from repositories.api_repo import AICAAPIRepository
from repositories.chat_repo import ChatRepository
from repositories.position_repo import PositionRepository
from repositories.user_repo import UserRepository
from services.base_service import BaseService
from utils.crypt import decrypt
from utils.enum import EncryptKeyType


class PositionService(BaseService):
    """
    ポジション関連操作(APIリクエストやキャッシュ保存/取得)サービス
    """

    def __init__(
        self,
        position_repository: PositionRepository,
        aica_api_repository: AICAAPIRepository,
        chat_repository: ChatRepository,
        user_repository: UserRepository,
        action_log_repository: ActionLogRepository,
    ) -> None:
        super().__init__()

        self._position_repository = position_repository
        self._aica_api_repository = aica_api_repository
        self._chat_repository = chat_repository
        self._user_repository = user_repository
        self._action_log_repository = action_log_repository

    async def get_position_detail(
        self,
        position_id: str,
        encrypted: bool = True,
    ) -> dict | None:
        """
        ポジション詳細はそんなに頻繁に更新されるわけではないし
        同じ会話中でしたらそんなに時間が経ってないはず
        なので、キャッシュにこの会話で取得済みのポジションがありましたら、利用し、
        なければ、APIサーバから取得します。

        Args:
            position_id: ポジションID
            encrypted: 暗号化されたポジションIDか否か

        Returns:
            ポジション詳細APIレスポンス
        """
        if encrypted:
            try:
                position_id = decrypt(EncryptKeyType.POSITION, position_id)
            except Exception:
                self.logger.exception(
                    "ポジションID復号化が失敗しました: %s",
                    position_id,
                )
                return None

        position_detail = self._position_repository.get_position_detail(
            position_id,
        )

        if not position_detail:
            api_path = f"positions/detail/{position_id}"
            self.logger.debug("ポジション詳細APIリクエスト: %s", api_path)
            _, position_detail = await self._aica_api_repository.post(api_path)

        if position_detail:
            self._position_repository.save_position_detail(
                position_id,
                position_detail,
            )
            applied_position_ids = (
                await asyncio.to_thread(self._user_repository.get_applied_position_ids) or []
            )
            position_detail["Applied"] = position_id in applied_position_ids

        return position_detail

    async def get_company_detail(
        self,
        position_id: str,
        encrypted: bool = True,
    ) -> dict | None:
        """
        会社詳細はそんなに頻繁に更新されるわけではないし
        同じ会話中でしたらそんなに時間が経ってないはず
        なので、キャッシュにこの会話で取得済みのポジションがありましたら、利用し、
        なければ、APIサーバから取得します。

        Args:
            position_id: ポジションID
            encrypted: 暗号化されたポジションIDか否か

        Returns:
            会社詳細APIレスポンス
        """
        if encrypted:
            try:
                position_id = decrypt(EncryptKeyType.POSITION, position_id)
            except Exception:
                self.logger.exception(
                    "ポジションID復号化が失敗しました: %s",
                    position_id,
                )
                return None

        company_detail = self._position_repository.get_company_detail(position_id)

        if not company_detail:
            api_path = f"companies/detail/position_id/{position_id}"
            self.logger.debug("会社詳細APIリクエスト: %s", api_path)
            _, company_detail = await self._aica_api_repository.get(api_path)

        if company_detail:
            self._position_repository.save_company_detail(
                position_id,
                company_detail,
            )
        return company_detail

    async def get_business_detail(
        self,
        position_id: str,
        encrypted: bool = True,
    ) -> dict | None:
        """
        キャッシュから業界詳細APIレスポンスを取得

        Args:
            position_id: ポジションID
            encrypted: 暗号化されたポジションIDか否か

        Returns:
            業界詳細APIレスポンス
        """
        if encrypted:
            try:
                position_id = decrypt(EncryptKeyType.POSITION, position_id)
            except Exception:
                self.logger.exception(
                    "ポジションID復号化が失敗しました: %s",
                    position_id,
                )
                return None

        business_detail = self._position_repository.get_business_detail(position_id)
        if not business_detail:
            api_path = f"businesses/detail/position_id/{position_id}"
            self.logger.debug("業界詳細APIリクエスト: %s", api_path)
            _, business_detail = await self._aica_api_repository.get(api_path)

        if business_detail:
            self._position_repository.save_business_detail(
                position_id,
                business_detail,
            )
        return business_detail

    async def get_position_recommendation(
        self,
        encrypted_theme: str,
    ) -> list[dict] | None:
        """
        APIサーバーからおすすめポジションを取得する

        Args:
            encrypted_theme: 暗号化されたおすすめテーマ
            search_conditions: ユーザーの検索条件

        Returns:
            おすすめのポジションリスト
        """
        theme = decrypt(
            EncryptKeyType.POSITION,
            encrypted_theme,
        )
        if not theme:
            return None

        api_path = f"positions/recommendations/{theme}"
        self.logger.debug("おすすめポジションAPIリクエスト: %s", api_path)
        _, response_data = await self._aica_api_repository.get(api_path)

        if not response_data or "Positions" not in response_data:
            return None

        # 分析用のログ出力
        all_positions = response_data.get("AllPositionIds", [])
        await asyncio.to_thread(
            self._action_log_repository.insert,
            log_type=ActionLogType.RECOMMENDATION,
            source=theme,
            content={
                "count": len(all_positions) if all_positions else 0,
            },
        )

        return self._position_repository.process_and_cache_positions(
            response_data["Positions"]
        )

    async def search_positions_by_tool_call_id(
        self,
        tool_call_id: str,
    ) -> dict[str, Any] | None:
        """
        ツールINPUTよりAPIサーバーからポジションを検索する

        Args:
            tool_call_id: ツールコールID。

        Returns:
            ポジション検索結果
        """
        search_conditions = await asyncio.to_thread(
            self._chat_repository.get_tool_input,
            tool_call_id,
        )
        if search_conditions:
            search_conditions.pop("RequestID", None)
            search_conditions.pop("SessionID", None)
        else:
            self.logger.error("ツールINPUTが取得できませんでした: %s", tool_call_id)
            return None

        api_path = "positions/search"
        self.logger.debug("ポジション検索APIリクエスト: %s", api_path)
        _, response_data = await self._aica_api_repository.post(
            api_path,
            json=search_conditions,
        )

        if not response_data or "Positions" not in response_data:
            return None

        # 分析用のログ出力
        await asyncio.to_thread(
            self._action_log_repository.insert,
            log_type=ActionLogType.POSITION_SEARCH_RESULT,
            source=tool_call_id,
            content=response_data,
        )

        position_search_result = (
            self._position_repository.process_position_search_result(
                tool_call_id,
                response_data,
            )
        )

        return position_search_result

    async def jobtype_specific_position_search(
        self,
        search_conditions: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        職種別検索

        Args:
            search_conditions: 検索条件

        Returns:
            ポジション検索結果
        """
        api_path = "positions/search/jobtype_specific"
        self.logger.debug("職種別ポジション検索APIリクエスト: %s", api_path)
        _, response_data = await self._aica_api_repository.post(
            api_path,
            json=search_conditions,
        )

        if not response_data or "Positions" not in response_data:
            return None

        # 分析用のログ出力
        await asyncio.to_thread(
            self._action_log_repository.insert,
            log_type=ActionLogType.POSITION_SEARCH_RESULT,
            source="jobtype_specific_position_search",
            content=response_data,
        )

        position_search_result = (
            self._position_repository.process_position_search_result(
                str(uuid.uuid4()),
                response_data,
            )
        )

        return position_search_result

    async def load_more(
        self,
        search_key: str,
        offset: int,
        limit: int,
    ) -> tuple[int, list[dict]]:
        """
        指定した検索キーに対して、ポジションIDのリストからoffsetとlimitでポジションサマリを取得する。

        Args:
            search_key: 検索キー（tool_call_id）
            offset: 取得開始位置
            limit: 取得件数

        Returns:
            有効なポジションID数、ポジションサマリリスト
        """
        all_position_ids = self._position_repository.get_cached_position_search_result(
            search_key,
        )
        if not all_position_ids:
            tool_output_str = await asyncio.to_thread(
                self._chat_repository.get_tool_output, search_key
            )
            tool_output_json = json.loads(tool_output_str)
            position_search_result_str = tool_output_json.get("text")
            if not position_search_result_str:
                self.logger.error(
                    "ポジション検索結果が取得できませんでした: %s",
                    search_key,
                )

            try:
                position_search_result_json = json.loads(position_search_result_str)
            except json.JSONDecodeError:
                self.logger.exception(
                    "ポジション検索結果(tool_call_id: %s)のJSONパースに失敗しました: %s",
                    search_key,
                    position_search_result_str,
                )

            all_position_ids = position_search_result_json.get("AllPositionIds")

            if not all_position_ids:
                self.logger.error(
                    "ポジション検索結果(tool_call_id: %s)にAllPositionIdsが存在しません: %s",
                    search_key,
                    position_search_result_str,
                )
                return 0, []

            self._position_repository.save_search_result_position_ids(
                search_key,
                all_position_ids,
            )

        position_ids = all_position_ids[offset : offset + limit]

        api_path = "positions/summaries"
        self.logger.debug("ポジションもっとみるAPIリクエスト: %s", api_path)
        _, response_data = await self._aica_api_repository.post(
            api_path,
            json={"PositionIDs": position_ids},
        )

        if not response_data or "Positions" not in response_data:
            # メモリから無効なポジションID消してから有効なポジションID数を返す
            count = self._position_repository.remove_search_result_positions_ids(
                search_key,
                position_ids,
            )
            return count, []

        positions = response_data["Positions"]
        returned_ids = {p["ID"] for p in positions}
        # サマリが取れなかったポジションID
        non_avaible_position_ids = [
            pid for pid in position_ids if pid not in returned_ids
        ]
        positions = self._position_repository.process_and_cache_positions(
            positions,
        )

        # サマリが取れなかったポジションIDがある場合、メモリから消してから有効なポジションID数を返す
        count = (
            self._position_repository.remove_search_result_positions_ids(
                search_key,
                non_avaible_position_ids,
            )
            if non_avaible_position_ids
            else len(position_ids)
        )

        return count, positions

    async def update_jobtypes(self, jobtypes) -> str | None:
        api_path = "positions/jobtypes/decided"
        payload = {
            "JobtypeNames": jobtypes,
        }

        self.logger.debug("職種決定APIリクエスト: %s", api_path)
        _, response_data = await self._aica_api_repository.post(
            api_path,
            json=payload,
        )

        if not isinstance(response_data, dict):
            return None

        tool_name = response_data.get("ToolName")
        if not isinstance(tool_name, str):
            return None

        normalized_tool_name = tool_name.strip()
        return normalized_tool_name or None

    async def clear_jobtypes(self):
        api_path = "positions/jobtypes/clear"
        self.logger.debug("職種リセットAPIリクエスト: %s", api_path)
        await self._aica_api_repository.post(api_path)

        return

    async def jobtype_other_filter(
        self,
        jobtype_name: str,
    ) -> dict[str, Any] | list[Any] | None:
        """
        指定職種の詳細検索条件取得

        Args:
            jobtype_name: クライアントからの職種名

        Returns:
            指定職種の詳細検索条件
        """
        api_path = "positions/search_filter/jobtype"
        self.logger.debug("職種別詳細検索条件APIリクエスト: %s", api_path)
        _, response_data = await self._aica_api_repository.get(
            api_path,
            params={"JobtypeName": jobtype_name},
        )
        return response_data

    async def current_search_filter(
        self,
    ) -> dict[str, Any] | list[Any] | None:
        """
        最新ポジション検索条件取得

        Returns:
            最新ポジション検索条件
        """
        api_path = "positions/search_filter/current"
        self.logger.debug("最新ポジション検索条件APIリクエスト: %s", api_path)
        _, response_data = await self._aica_api_repository.get(api_path)
        return response_data
