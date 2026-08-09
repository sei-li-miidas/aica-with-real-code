from __future__ import annotations

import asyncio
import copy
import datetime
import json
import logging
import random
import uuid
from pathlib import Path
from typing import Any

from client.aica_client import AICAClient
from models import (
    ApplyMode,
    ChatRequestPayload,
    ChatRequestType,
    ChatResponseType,
    FinishPolicy,
    FilterStateSnapshot,
    HeadlessPersonaSeed,
    HeadlessState,
    HistoryRecord,
    LLMMessageRole,
    PageName,
    PositionSelectionStrategy,
    ResponseExchange,
    SessionStatus,
)
from utils.const import (
    LOGGER_PREFIX,
    POSITION_BACK_TO_CHAT_PROMPT,
    SOURCE_COMPONENT_POSITION,
    SOURCE_COMPONENT_RECOMMENDATION,
)
from utils.http import HeadlessAPIClient


class E2EClient:
    SYSTEM_ERROR_MESSAGE = "システムエラーが発生しました。"

    def __init__(
        self,
        ws_url: str,
        api_url: str,
        model: Any,
        system_prompt: str,
        max_rounds: int | None,
        client_id: str,
        model_name: str,
        persona_seed: HeadlessPersonaSeed,
        finish_policy: FinishPolicy,
        auto_follow_position_search_link: bool = True,
        auto_run_profile_apply: bool = True,
        restore_history_on_restart: bool = True,
        random_disconnect_probability: float = 0.0,
        resume_session_id: str | None = None,
        debug_mode: bool = False,
    ):
        """
        E2Eクライアントを初期化する。

        Args:
            ws_url (str): キャリアアドバイザーのWebSocket URL
            api_url (str): キャリアアドバイザーのAPI URL
            model (Any): 求職者LLMモデル
            system_prompt (str): 求職者システムプロンプト
            max_rounds (int | None): 最大会話数
            client_id (str): クライアント識別子
            model_name (str): ログ出力用モデル名
            persona_seed (HeadlessPersonaSeed): 入力データ生成用シード
            finish_policy (FinishPolicy): 実行終了ポリシー
            auto_follow_position_search_link (bool): position_search_link を自動追従するか
            auto_run_profile_apply (bool): プロフィール登録と応募を自動実行するか
            restore_history_on_restart (bool): 再接続時に履歴復元を行うか
            random_disconnect_probability (float): ランダム切断確率（0.0-1.0）
            resume_session_id (str | None): 再開対象のsession_id
            debug_mode (bool): デバッグログを標準出力にも表示するか

        Returns:
            None
        """
        self.ws_url = ws_url
        self.api_url = api_url
        # Some runtime configs can pass null/empty max_rounds; treat it as unlimited.
        if max_rounds in (None, "", "null", "None"):
            self.max_rounds = 0
        else:
            try:
                self.max_rounds = max(int(max_rounds), 0)
            except (ValueError, TypeError):
                raise ValueError(
                    f"max_rounds must be a non-negative integer; got {max_rounds!r}"
                )
        self.client_id = client_id
        self.model_name = model_name
        self.debug_mode = debug_mode
        self.finish_policy = finish_policy
        self.auto_follow_position_search_link = auto_follow_position_search_link
        self.auto_run_profile_apply = auto_run_profile_apply
        self.restore_history_on_restart = restore_history_on_restart
        self.random_disconnect_probability = max(
            0.0, min(float(random_disconnect_probability), 1.0)
        )
        self.resume_session_id = resume_session_id
        self.seed = persona_seed

        self.client = AICAClient(ws_url, model, system_prompt, client_id)
        self.api_client = HeadlessAPIClient(api_url)
        self.logger = self._setup_logger()
        self.conversation_stats: list[dict[str, float]] = []
        self.state = HeadlessState(
            session_id=resume_session_id or "",
            terms_of_use_agreed=persona_seed.terms_of_use_agreed,
        )

    def _setup_logger(self) -> logging.Logger:
        """
        実行ごとのファイルロガーを生成する。

        Returns:
            logging.Logger: 設定済みロガー
        """
        logs_dir = Path("/tmp/e2e_client")
        logs_dir.mkdir(exist_ok=True)

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M%S") + f"{now.microsecond:03d}"[:3]
        unique_id = uuid.uuid4().hex
        log_filename = f"{self.client_id}_{self.model_name}_{timestamp}_{unique_id}.log"
        logger = logging.getLogger(
            f"{LOGGER_PREFIX}.client.{self.client_id}_{self.model_name}_{timestamp}_{unique_id}"
        )
        handler = logging.FileHandler(logs_dir / log_filename)
        handler.setFormatter(
            logging.Formatter(
                f"[%(asctime)s] [%(levelname)s] [{self.client_id} ({self.model_name})]: %(message)s"
            )
        )
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        return logger

    def _log_info(self, message: str, console: bool = False) -> None:
        """
        ログを出力する。

        Args:
            message (str): 出力メッセージ
            console (bool): True の場合は標準出力にも表示する

        Returns:
            None
        """
        self.logger.info(message)
        if self.debug_mode or console:
            print(f"{self.client_id} ({self.model_name}) {message}")

    def _log_action(self, action: str, **fields: Any) -> None:
        """
        構造化されたアクションログを出力する。

        Args:
            action (str): アクション名
            **fields (Any): 付加情報

        Returns:
            None
        """
        details = ", ".join(f"{key}={value}" for key, value in fields.items())
        message = f"[action] {action}"
        if details:
            message = f"{message}: {details}"
        self._log_info(message)

    def _session_log_context(self) -> str:
        """
        現在セッションのログ表示用コンテキスト文字列を返す。

        Returns:
            str: ログ出力用コンテキスト文字列
        """
        return f"session_id={self.state.session_id or 'unknown'}"

    def _next_message_id(self, prefix: str) -> str:
        """
        指定プレフィックス付きの一意なメッセージIDを生成する。

        Args:
            prefix (str): メッセージIDのプレフィックス

        Returns:
            str: 生成されたメッセージID
        """
        return f"{prefix}_{uuid.uuid4()}"

    def _history_bucket(self, position_id: str | None) -> list[dict[str, Any]]:
        """
        position_id に対応する履歴バケットを返す。

        Args:
            position_id (str | None): ポジションID。None の場合はメイン履歴を返す。

        Returns:
            list[dict[str, Any]]: 対応する履歴バケット
        """
        if position_id:
            return self.state.position_histories.setdefault(position_id, [])
        return self.state.main_history

    def _append_history_item(
        self, position_id: str | None, item: dict[str, Any]
    ) -> None:
        """
        履歴アイテムを追記し、同一message_idは追記マージする。

        Args:
            position_id (str | None): ポジションID。None はメイン履歴対象。
            item (dict[str, Any]): 追記する履歴アイテム

        Returns:
            None
        """
        bucket = self._history_bucket(position_id)
        for existing in bucket:
            if existing["message_id"] != item["message_id"]:
                continue
            if existing["type"] == ChatResponseType.MESSAGE:
                existing["message"] += item["message"]
            else:
                existing["message"] = item["message"]
            return
        bucket.append(item)

    def _merge_position_snapshot(
        self, position_id: str | int, data: dict[str, Any]
    ) -> None:
        """
        ポジション情報スナップショットをID単位でマージ保存する。

        Args:
            position_id (str | int): ポジションID
            data (dict[str, Any]): マージするポジション情報

        Returns:
            None
        """
        key = str(position_id)
        existing = self.state.positions.get(key, {})
        self.state.positions[key] = {**existing, **data}

    def _normalize_position_ids(
        self, position_ids: list[str | int | None]
    ) -> list[str]:
        """
        空値を除外してポジションID一覧を文字列化する。

        Args:
            position_ids (list[str | int | None]): 正規化するポジションID一覧

        Returns:
            list[str]: 空値を除外した文字列ID一覧
        """
        normalized: list[str] = []
        for position_id in position_ids:
            if position_id in (None, ""):
                continue
            normalized.append(str(position_id))
        return normalized

    def _raise_contract_error(
        self,
        category: str,
        source: str,
        details: str,
        actual: Any | None = None,
    ) -> None:
        actual_repr = ""
        if actual is not None:
            actual_repr = f", actual={actual!r}"
        raise RuntimeError(
            f"{category}: source={source}, details={details}{actual_repr}, "
            f"{self._session_log_context()}"
        )

    def _require_contract(
        self,
        condition: bool,
        *,
        category: str,
        source: str,
        details: str,
        actual: Any | None = None,
    ) -> None:
        if not condition:
            self._raise_contract_error(category, source, details, actual)

    def _normalize_jobtype_option(self, option: Any) -> dict[str, Any]:
        self._require_contract(
            isinstance(option, dict),
            category="rest_format_invalid",
            source="jobtype_option",
            details="jobtype option must be object",
            actual=option,
        )
        label = option.get("Label", option.get("Value"))
        value = option.get("Value", option.get("Label"))
        description = option.get("Description", "")
        selected = bool(option.get("Selected", False))
        self._require_contract(
            isinstance(label, str) and label != "",
            category="rest_format_invalid",
            source="jobtype_option",
            details="jobtype option Label must be non-empty string",
            actual=option,
        )
        self._require_contract(
            isinstance(value, str) and value != "",
            category="rest_format_invalid",
            source="jobtype_option",
            details="jobtype option Value must be non-empty string",
            actual=option,
        )
        self._require_contract(
            isinstance(description, str),
            category="rest_format_invalid",
            source="jobtype_option",
            details="jobtype option Description must be string",
            actual=option,
        )
        return {
            "Label": label,
            "Value": value,
            "Description": description,
            "Selected": selected,
        }

    def _normalize_location_option(self, option: Any, source: str) -> dict[str, Any]:
        self._require_contract(
            isinstance(option, dict),
            category="rest_format_invalid",
            source=source,
            details="location option must be object",
            actual=option,
        )
        label = option.get("Label")
        value = option.get("Value")
        prefecture_name = option.get("PrefectureName", "")
        city_name = option.get("CityName", "")
        if not isinstance(prefecture_name, str):
            prefecture_name = ""
        if not isinstance(city_name, str):
            city_name = ""
        derived_value = f"{prefecture_name}{city_name}"
        if not isinstance(label, str) or not label:
            label = derived_value
        if not isinstance(value, str) or not value:
            value = derived_value or label
        self._require_contract(
            value != "",
            category="rest_format_invalid",
            source=source,
            details="location option must have Value or PrefectureName/CityName",
            actual=option,
        )
        return {
            "Label": label,
            "Value": value,
            "Selected": bool(option.get("Selected", False)),
            "PrefectureName": prefecture_name,
            "CityName": city_name,
        }

    def _normalize_other_filter_option(
        self, option: Any, source: str
    ) -> dict[str, str]:
        self._require_contract(
            isinstance(option, dict),
            category="rest_format_invalid",
            source=source,
            details="other filter option must be object",
            actual=option,
        )
        label = option.get("Label")
        value = option.get("Value")
        self._require_contract(
            isinstance(label, str) and label != "",
            category="rest_format_invalid",
            source=source,
            details="other filter option Label must be non-empty string",
            actual=option,
        )
        self._require_contract(
            isinstance(value, str) and value != "",
            category="rest_format_invalid",
            source=source,
            details="other filter option Value must be non-empty string",
            actual=option,
        )
        return {"Label": label, "Value": value}

    def _normalize_other_filter(self, item: Any, source: str) -> dict[str, Any]:
        self._require_contract(
            isinstance(item, dict),
            category="rest_format_invalid",
            source=source,
            details="other filter must be object",
            actual=item,
        )
        key = item.get("Key")
        name = item.get("Name")
        filter_type = item.get("Type")
        options = item.get("Options")
        self._require_contract(
            isinstance(key, str) and key != "",
            category="rest_format_invalid",
            source=source,
            details="other filter Key must be non-empty string",
            actual=item,
        )
        self._require_contract(
            isinstance(name, str) and name != "",
            category="rest_format_invalid",
            source=source,
            details="other filter Name must be non-empty string",
            actual=item,
        )
        self._require_contract(
            isinstance(filter_type, str),
            category="rest_format_invalid",
            source=source,
            details="other filter Type must be string",
            actual=item,
        )
        filter_type_aliases = {
            "single_select": "single",
            "multi_select": "multiple",
        }
        normalized_filter_type = filter_type_aliases.get(filter_type, filter_type)
        self._require_contract(
            normalized_filter_type in ("single", "multiple"),
            category="rest_format_invalid",
            source=source,
            details="other filter Type must be single|multiple",
            actual=item,
        )
        self._require_contract(
            isinstance(options, list),
            category="rest_format_invalid",
            source=source,
            details="other filter Options must be list",
            actual=item,
        )
        return {
            "Key": key,
            "Name": name,
            "Type": normalized_filter_type,
            "Options": [
                self._normalize_other_filter_option(option, source)
                for option in options
            ],
        }

    def _normalize_grouped_jobtypes(
        self, grouped: Any, source: str, tool_name: str = ""
    ) -> dict[str, list[dict[str, Any]]]:
        if isinstance(grouped, list):
            effective_tool_name = tool_name or self.state.active_tool_name
            self._require_contract(
                effective_tool_name != "",
                category="rest_format_invalid",
                source=source,
                details="active_tool_name is required when Jobtypes is list",
                actual=grouped,
            )
            grouped = {effective_tool_name: grouped}
        self._require_contract(
            isinstance(grouped, dict),
            category="rest_format_invalid",
            source=source,
            details="Jobtypes must be object",
            actual=grouped,
        )
        normalized: dict[str, list[dict[str, Any]]] = {}
        for tool_name, options in grouped.items():
            self._require_contract(
                isinstance(tool_name, str) and tool_name != "",
                category="rest_format_invalid",
                source=source,
                details="Jobtypes group key must be non-empty string",
                actual=tool_name,
            )
            self._require_contract(
                isinstance(options, list),
                category="rest_format_invalid",
                source=source,
                details=f"Jobtypes[{tool_name}] must be list",
                actual=options,
            )
            normalized[tool_name] = [
                self._normalize_jobtype_option(option) for option in options
            ]
        return normalized

    def _normalize_grouped_other_filters(
        self, grouped: Any, source: str, tool_name: str = ""
    ) -> dict[str, list[dict[str, Any]]]:
        if grouped in (None, {}):
            return {}
        if isinstance(grouped, list):
            effective_tool_name = tool_name or self.state.active_tool_name
            self._require_contract(
                effective_tool_name != "",
                category="rest_format_invalid",
                source=source,
                details="active_tool_name is required when OtherFilters is list",
                actual=grouped,
            )
            grouped = {effective_tool_name: grouped}
        self._require_contract(
            isinstance(grouped, dict),
            category="rest_format_invalid",
            source=source,
            details="OtherFilters must be object",
            actual=grouped,
        )
        normalized: dict[str, list[dict[str, Any]]] = {}
        for tool_name, filters in grouped.items():
            self._require_contract(
                isinstance(tool_name, str) and tool_name != "",
                category="rest_format_invalid",
                source=source,
                details="OtherFilters group key must be non-empty string",
                actual=tool_name,
            )
            self._require_contract(
                isinstance(filters, list),
                category="rest_format_invalid",
                source=source,
                details=f"OtherFilters[{tool_name}] must be list",
                actual=filters,
            )
            normalized[tool_name] = [
                self._normalize_other_filter(item, source) for item in filters
            ]
        return normalized

    def _normalize_selected_filter_options(
        self, grouped: Any, source: str
    ) -> dict[str, dict[str, list[str]]]:
        if grouped in (None, {}):
            return {}
        self._require_contract(
            isinstance(grouped, dict),
            category="rest_format_invalid",
            source=source,
            details="SelectedFilterOptions must be object",
            actual=grouped,
        )
        normalized: dict[str, dict[str, list[str]]] = {}
        for tool_name, groups in grouped.items():
            self._require_contract(
                isinstance(tool_name, str) and tool_name != "",
                category="rest_format_invalid",
                source=source,
                details="SelectedFilterOptions tool key must be non-empty string",
                actual=tool_name,
            )
            self._require_contract(
                isinstance(groups, dict),
                category="rest_format_invalid",
                source=source,
                details=f"SelectedFilterOptions[{tool_name}] must be object",
                actual=groups,
            )
            normalized[tool_name] = {}
            for filter_name, values in groups.items():
                self._require_contract(
                    isinstance(filter_name, str) and filter_name != "",
                    category="rest_format_invalid",
                    source=source,
                    details="SelectedFilterOptions filter name must be non-empty string",
                    actual=filter_name,
                )
                self._require_contract(
                    isinstance(values, list)
                    and all(isinstance(value, str) for value in values),
                    category="rest_format_invalid",
                    source=source,
                    details=f"SelectedFilterOptions[{tool_name}][{filter_name}] must be string[]",
                    actual=values,
                )
                normalized[tool_name][filter_name] = list(values)
        return normalized

    def _normalize_same_filter_jobtypes(
        self, grouped: Any, source: str, tool_name: str = ""
    ) -> dict[str, list[str]]:
        if grouped in (None, {}):
            return {}
        if isinstance(grouped, list):
            effective_tool_name = tool_name or self.state.active_tool_name
            self._require_contract(
                effective_tool_name != "",
                category="rest_format_invalid",
                source=source,
                details="active_tool_name is required when JobtypeNamesWithSameSearchFilters is list",
                actual=grouped,
            )
            self._require_contract(
                all(isinstance(name, str) for name in grouped),
                category="rest_format_invalid",
                source=source,
                details="JobtypeNamesWithSameSearchFilters list must be string[]",
                actual=grouped,
            )
            return {effective_tool_name: list(grouped)}
        self._require_contract(
            isinstance(grouped, dict),
            category="rest_format_invalid",
            source=source,
            details="JobtypeNamesWithSameSearchFilters must be object",
            actual=grouped,
        )
        normalized: dict[str, list[str]] = {}
        for tool_name, names in grouped.items():
            self._require_contract(
                isinstance(tool_name, str) and tool_name != "",
                category="rest_format_invalid",
                source=source,
                details="JobtypeNamesWithSameSearchFilters tool key must be non-empty string",
                actual=tool_name,
            )
            self._require_contract(
                isinstance(names, list)
                and all(isinstance(name, str) for name in names),
                category="rest_format_invalid",
                source=source,
                details=f"JobtypeNamesWithSameSearchFilters[{tool_name}] must be string[]",
                actual=names,
            )
            normalized[tool_name] = list(names)
        return normalized

    def _normalize_search_filters(
        self, filters: Any, source: str, tool_name: str = ""
    ) -> dict[str, Any]:
        self._require_contract(
            isinstance(filters, dict),
            category="rest_format_invalid",
            source=source,
            details="SearchFilters must be object",
            actual=filters,
        )
        grouped_jobtypes = self._normalize_grouped_jobtypes(
            filters.get("Jobtypes", {}),
            source,
            tool_name,
        )
        locations = filters.get("Locations") or {}
        self._require_contract(
            isinstance(locations, dict),
            category="rest_format_invalid",
            source=source,
            details="Locations must be object",
            actual=locations,
        )
        residence = locations.get("Residence")
        residence_prefecture_name = ""
        residence_city_name = ""
        commuting_areas: list[dict[str, Any]] = []
        if residence is not None:
            self._require_contract(
                isinstance(residence, dict),
                category="rest_format_invalid",
                source=source,
                details="Locations.Residence must be object",
                actual=residence,
            )
            address = residence.get("Address")
            if address is not None:
                self._require_contract(
                    isinstance(address, dict),
                    category="rest_format_invalid",
                    source=source,
                    details="Locations.Residence.Address must be object",
                    actual=address,
                )
                prefecture_name = address.get("PrefectureName", "")
                city_name = address.get("CityName", "")
                self._require_contract(
                    isinstance(prefecture_name, str) and isinstance(city_name, str),
                    category="rest_format_invalid",
                    source=source,
                    details="Locations.Residence.Address PrefectureName/CityName must be strings",
                    actual=address,
                )
                residence_prefecture_name = prefecture_name
                residence_city_name = city_name
            commuting_areas = [
                self._normalize_location_option(option, source)
                for option in (residence.get("CommutingAreas") or [])
            ]

        work_locations = [
            self._normalize_location_option(option, source)
            for option in locations.get("WorkLocations", []) or []
        ]
        remote_work_possible = locations.get("RemoteWorkPossible")
        if remote_work_possible is not None:
            self._require_contract(
                isinstance(remote_work_possible, bool),
                category="rest_format_invalid",
                source=source,
                details="Locations.RemoteWorkPossible must be boolean when present",
                actual=remote_work_possible,
            )

        salary = filters.get("Salary", 0)
        self._require_contract(
            isinstance(salary, int) and not isinstance(salary, bool),
            category="rest_format_invalid",
            source=source,
            details="Salary must be integer",
            actual=salary,
        )

        position_keyword = filters.get("PositionKeyword", "")
        if position_keyword is None:
            position_keyword = ""
        self._require_contract(
            isinstance(position_keyword, str),
            category="rest_format_invalid",
            source=source,
            details="PositionKeyword must be string when present",
            actual=position_keyword,
        )

        return {
            "Jobtypes": grouped_jobtypes,
            "Salary": salary,
            "PositionKeyword": position_keyword,
            "Locations": {
                "Residence": {
                    "Address": {
                        "PrefectureName": residence_prefecture_name,
                        "CityName": residence_city_name,
                    },
                    "CommutingAreas": commuting_areas,
                }
                if residence is not None
                else None,
                "WorkLocations": work_locations,
                "RemoteWorkPossible": remote_work_possible,
            },
            "OtherFilters": self._normalize_grouped_other_filters(
                filters.get("OtherFilters"),
                source,
                tool_name,
            ),
            "SelectedFilterOptions": self._normalize_selected_filter_options(
                filters.get("SelectedFilterOptions"),
                source,
            ),
        }

    def _validate_position_search_link_payload(
        self, payload: Any, source: str
    ) -> dict[str, Any]:
        self._require_contract(
            isinstance(payload, dict),
            category="rest_format_invalid",
            source=source,
            details="position_search_link payload must be object",
            actual=payload,
        )
        tool_call_id = payload.get("ToolCallId")
        self._require_contract(
            isinstance(tool_call_id, str) and tool_call_id != "",
            category="rest_format_invalid",
            source=source,
            details="ToolCallId must be non-empty string",
            actual=payload,
        )
        self._require_contract(
            isinstance(payload.get("Salary"), int)
            and not isinstance(payload.get("Salary"), bool),
            category="rest_format_invalid",
            source=source,
            details="Salary must be integer",
            actual=payload,
        )
        residence = payload.get("Residence")
        self._require_contract(
            isinstance(residence, str),
            category="rest_format_invalid",
            source=source,
            details="Residence must be string",
            actual=payload,
        )
        position_keyword = payload.get("PositionKeyword")
        if position_keyword is None:
            position_keyword = ""
        self._require_contract(
            isinstance(position_keyword, str),
            category="rest_format_invalid",
            source=source,
            details="PositionKeyword must be string",
            actual=payload,
        )
        payload["PositionKeyword"] = position_keyword
        jobtype_names = payload.get("JobtypeNames") or []
        self._require_contract(
            isinstance(jobtype_names, list)
            and all(isinstance(item, str) for item in jobtype_names),
            category="rest_format_invalid",
            source=source,
            details="JobtypeNames must be string[]",
            actual=payload,
        )
        work_locations = payload.get("WorkLocations") or []
        self._require_contract(
            isinstance(work_locations, list)
            and all(isinstance(item, str) for item in work_locations),
            category="rest_format_invalid",
            source=source,
            details="WorkLocations must be string[]",
            actual=payload,
        )
        self._require_contract(
            isinstance(payload.get("IsFullyRemoteWork"), bool),
            category="rest_format_invalid",
            source=source,
            details="IsFullyRemoteWork must be boolean",
            actual=payload,
        )
        return payload

    def _validate_jobtype_search_result_payload(
        self, payload: Any, source: str
    ) -> dict[str, Any]:
        self._require_contract(
            isinstance(payload, dict),
            category="rest_format_invalid",
            source=source,
            details="jobtype_search_result payload must be object",
            actual=payload,
        )
        tool_call_id = payload.get("ToolCallId")
        if tool_call_id is not None:
            self._require_contract(
                isinstance(tool_call_id, str) and tool_call_id != "",
                category="rest_format_invalid",
                source=source,
                details="ToolCallId must be non-empty string when present",
                actual=payload,
            )
        self._require_contract(
            isinstance(payload.get("Jobtypes"), list),
            category="rest_format_invalid",
            source=source,
            details="Jobtypes must be list",
            actual=payload,
        )
        normalized_jobtypes = []
        for item in payload.get("Jobtypes", []):
            self._require_contract(
                isinstance(item, dict),
                category="rest_format_invalid",
                source=source,
                details="Jobtypes item must be object",
                actual=item,
            )
            item_id = item.get("ID")
            item_name = item.get("Name")
            self._require_contract(
                isinstance(item_id, str) and item_id != "",
                category="rest_format_invalid",
                source=source,
                details="Jobtypes item ID must be non-empty string",
                actual=item,
            )
            self._require_contract(
                isinstance(item_name, str),
                category="rest_format_invalid",
                source=source,
                details="Jobtypes item Name must be string",
                actual=item,
            )
            normalized_jobtypes.append({"ID": item_id, "Name": item_name})
        payload["Jobtypes"] = normalized_jobtypes
        choice = payload.get("Choice")
        if choice is not None:
            self._require_contract(
                isinstance(choice, str),
                category="rest_format_invalid",
                source=source,
                details="Choice must be string when present",
                actual=choice,
            )
        keyword = payload.get("Keyword")
        if keyword is not None:
            self._require_contract(
                isinstance(keyword, str),
                category="rest_format_invalid",
                source=source,
                details="Keyword must be string when present",
                actual=keyword,
            )
        choice = payload.get("Choice")
        if choice is not None:
            self._require_contract(
                isinstance(choice, str),
                category="rest_format_invalid",
                source=source,
                details="Choice must be string when present",
                actual=payload,
            )
        return payload

    def _validate_position_summary(self, item: Any, source: str) -> dict[str, Any]:
        self._require_contract(
            isinstance(item, dict),
            category="rest_format_invalid",
            source=source,
            details="position summary must be object",
            actual=item,
        )
        self._require_contract(
            item.get("ID") not in (None, ""),
            category="rest_format_invalid",
            source=source,
            details="position summary ID must exist",
            actual=item,
        )
        for key in ("Title", "MainJobText", "SalaryFrom", "SalaryTo", "Image"):
            value = item.get(key)
            if value is not None:
                self._require_contract(
                    isinstance(value, (str, int, float))
                    and not isinstance(value, bool),
                    category="rest_format_invalid",
                    source=source,
                    details=f"position summary {key} must be primitive when present",
                    actual=item,
                )
        return item

    def _validate_position_search_result_payload(
        self, payload: Any, source: str
    ) -> dict[str, Any]:
        self._require_contract(
            isinstance(payload, dict),
            category="rest_format_invalid",
            source=source,
            details="position search payload must be object",
            actual=payload,
        )
        positions = payload.get("Positions")
        self._require_contract(
            isinstance(positions, list),
            category="rest_format_invalid",
            source=source,
            details="Positions must be list",
            actual=payload,
        )
        search_key = payload.get("SearchKey")
        if search_key is not None:
            self._require_contract(
                isinstance(search_key, str),
                category="rest_format_invalid",
                source=source,
                details="SearchKey must be string when present",
                actual=payload,
            )
        total_position_count = payload.get("TotalPositionCount")
        if total_position_count is not None:
            self._require_contract(
                isinstance(total_position_count, int)
                and not isinstance(total_position_count, bool),
                category="rest_format_invalid",
                source=source,
                details="TotalPositionCount must be integer when present",
                actual=payload,
            )
        for item in positions:
            self._validate_position_summary(item, source)
        recommendations = payload.get("Recommendations")
        if recommendations is not None:
            self._require_contract(
                isinstance(recommendations, list),
                category="rest_format_invalid",
                source=source,
                details="Recommendations must be list when present",
                actual=payload,
            )
            for recommendation in recommendations:
                self._require_contract(
                    isinstance(recommendation, dict),
                    category="rest_format_invalid",
                    source=source,
                    details="Recommendation item must be object",
                    actual=recommendation,
                )
                self._require_contract(
                    isinstance(recommendation.get("Theme"), str),
                    category="rest_format_invalid",
                    source=source,
                    details="Recommendation Theme must be string",
                    actual=recommendation,
                )
                self._require_contract(
                    isinstance(recommendation.get("Title"), str),
                    category="rest_format_invalid",
                    source=source,
                    details="Recommendation Title must be string",
                    actual=recommendation,
                )
                if recommendation.get("Description") is not None:
                    self._require_contract(
                        isinstance(recommendation.get("Description"), str),
                        category="rest_format_invalid",
                        source=source,
                        details="Recommendation Description must be string when present",
                        actual=recommendation,
                    )
        filters = payload.get("SearchFilters")
        if filters is not None:
            payload["SearchFilters"] = self._normalize_search_filters(filters, source)
        same_filters = payload.get("JobtypeNamesWithSameSearchFilters")
        if same_filters is not None:
            payload["JobtypeNamesWithSameSearchFilters"] = (
                self._normalize_same_filter_jobtypes(same_filters, source)
            )
        return payload

    def _normalize_current_search_filter_payload(
        self, payload: Any, source: str
    ) -> dict[str, Any]:
        self._require_contract(
            isinstance(payload, dict),
            category="rest_format_invalid",
            source=source,
            details="current search filter payload must be object",
            actual=payload,
        )
        tool_name = payload.get("ToolName", "")
        if tool_name is None:
            tool_name = ""
        self._require_contract(
            isinstance(tool_name, str),
            category="rest_format_invalid",
            source=source,
            details="ToolName must be string when present",
            actual=payload,
        )
        filters = payload.get("SearchFilters")
        if filters is None:
            return {
                "ToolName": tool_name,
                "SearchFilters": None,
                "JobtypeNamesWithSameSearchFilters": self._normalize_same_filter_jobtypes(
                    payload.get("JobtypeNamesWithSameSearchFilters"),
                    source,
                    tool_name,
                ),
            }
        return {
            "ToolName": tool_name,
            "SearchFilters": self._normalize_search_filters(filters, source, tool_name),
            "JobtypeNamesWithSameSearchFilters": self._normalize_same_filter_jobtypes(
                payload.get("JobtypeNamesWithSameSearchFilters"),
                source,
                tool_name,
            ),
        }

    def _normalize_jobtype_filter_payload(
        self, payload: Any, source: str
    ) -> dict[str, Any]:
        self._require_contract(
            isinstance(payload, dict),
            category="rest_format_invalid",
            source=source,
            details="jobtype filter payload must be object",
            actual=payload,
        )
        return {
            "OtherFilters": [
                self._normalize_other_filter(item, source)
                for item in payload.get("OtherFilters", []) or []
            ],
            "SelectedFilterOptions": self._normalize_selected_filter_options(
                {"tool": payload.get("SelectedFilterOptions", {})},
                source,
            ).get("tool", {}),
        }

    def _apply_normalized_search_filter_state(
        self,
        *,
        filters: dict[str, Any] | None,
        tool_name: str = "",
        same_filter_jobtypes: dict[str, list[str]] | None = None,
    ) -> None:
        if same_filter_jobtypes is not None:
            self.state.same_other_filter_jobtypes = copy.deepcopy(same_filter_jobtypes)
        if isinstance(tool_name, str):
            self.state.active_tool_name = tool_name
        if not filters:
            self.state.current_search_filters = {}
            self.state.jobtype_groups = {}
            self.state.salary = 0
            self.state.position_keyword = ""
            self.state.residence = ""
            self.state.residence_prefecture_name = ""
            self.state.residence_city_name = ""
            self.state.commuting_areas = []
            self.state.work_locations = []
            self.state.remote_work_possible = None
            self.state.other_filters = {}
            self.state.selected_filter_options = {}
            self.state.search_ready = False
            return

        self.state.current_search_filters = copy.deepcopy(filters)
        self.state.jobtype_groups = copy.deepcopy(filters.get("Jobtypes", {}))
        if self.state.active_tool_name == "" and len(self.state.jobtype_groups) == 1:
            self.state.active_tool_name = next(iter(self.state.jobtype_groups))
        self.state.salary = int(filters.get("Salary", 0) or 0)
        self.state.position_keyword = str(filters.get("PositionKeyword", "") or "")

        locations = filters.get("Locations", {})
        residence = locations.get("Residence")
        if isinstance(residence, dict):
            address = residence.get("Address") or {}
            self.state.residence_prefecture_name = str(
                address.get("PrefectureName", "") or ""
            )
            self.state.residence_city_name = str(address.get("CityName", "") or "")
            self.state.residence = f"{self.state.residence_prefecture_name}{self.state.residence_city_name}"
            self.state.commuting_areas = copy.deepcopy(
                residence.get("CommutingAreas", []) or []
            )
        else:
            self.state.residence = ""
            self.state.residence_prefecture_name = ""
            self.state.residence_city_name = ""
            self.state.commuting_areas = []
        self.state.work_locations = copy.deepcopy(
            locations.get("WorkLocations", []) or []
        )
        self.state.remote_work_possible = locations.get("RemoteWorkPossible")
        self.state.other_filters = copy.deepcopy(filters.get("OtherFilters", {}) or {})
        self.state.selected_filter_options = copy.deepcopy(
            filters.get("SelectedFilterOptions", {}) or {}
        )
        has_jobtypes = bool(self.state.jobtype_groups)
        has_location = bool(self.state.residence) or bool(self.state.work_locations)
        self.state.search_ready = (
            has_jobtypes and has_location and self.state.salary > 0
        )

    def _update_search_filter_state(
        self, payload: dict[str, Any] | None, *, source: str = "search_filter"
    ) -> None:
        """
        検索フィルタ関連の状態を payload から更新する。

        Args:
            payload (dict[str, Any] | None): 検索フィルタ情報を含む辞書

        Returns:
            None
        """
        if payload is None:
            return
        if "SearchFilters" in payload or "ToolName" in payload:
            normalized = self._normalize_current_search_filter_payload(payload, source)
            self._apply_normalized_search_filter_state(
                filters=normalized.get("SearchFilters"),
                tool_name=normalized.get("ToolName", ""),
                same_filter_jobtypes=normalized.get(
                    "JobtypeNamesWithSameSearchFilters", {}
                ),
            )
            return
        normalized_filters = self._normalize_search_filters(payload, source)
        same_filter_jobtypes = self._normalize_same_filter_jobtypes(
            payload.get("JobtypeNamesWithSameSearchFilters"),
            source,
        )
        self._apply_normalized_search_filter_state(
            filters=normalized_filters,
            tool_name=self.state.active_tool_name,
            same_filter_jobtypes=same_filter_jobtypes,
        )

    def _snapshot_filter_state(self) -> FilterStateSnapshot:
        return FilterStateSnapshot(
            active_tool_name=self.state.active_tool_name,
            jobtype_groups=copy.deepcopy(self.state.jobtype_groups),
            salary=self.state.salary,
            position_keyword=self.state.position_keyword,
            residence_prefecture_name=self.state.residence_prefecture_name,
            residence_city_name=self.state.residence_city_name,
            commuting_areas=copy.deepcopy(self.state.commuting_areas),
            work_locations=copy.deepcopy(self.state.work_locations),
            remote_work_possible=self.state.remote_work_possible,
            other_filters=copy.deepcopy(self.state.other_filters),
            selected_filter_options=copy.deepcopy(self.state.selected_filter_options),
            same_other_filter_jobtypes=copy.deepcopy(
                self.state.same_other_filter_jobtypes
            ),
        )

    async def _refresh_current_search_filter(self) -> None:
        """
        現在の検索条件をAPIから再取得して状態へ反映する。

        Returns:
            None
        """
        result = await self._api_get("positions/search_filter/current")
        if result.http_status != 200 or not isinstance(result.data, dict):
            return
        self._update_search_filter_state(
            result.data, source="positions/search_filter/current"
        )
        self._log_action(
            "current_search_filter_loaded",
            tool_name=self.state.active_tool_name,
            jobtype_groups=len(self.state.current_search_filters.get("Jobtypes", {}))
            if isinstance(self.state.current_search_filters, dict)
            else 0,
        )

    async def _api_get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        source_component: str | None = None,
    ):
        result = await self.api_client.get(
            path,
            params=params,
            source_component=source_component,
        )
        self._validate_rest_result(path, result)
        return result

    async def _api_post(
        self,
        path: str,
        *,
        data: Any | None = None,
        source_component: str | None = None,
    ):
        result = await self.api_client.post(
            path,
            data=data,
            source_component=source_component,
        )
        self._validate_rest_result(path, result)
        return result

    async def _api_put(
        self,
        path: str,
        *,
        data: Any | None = None,
        source_component: str | None = None,
    ):
        result = await self.api_client.put(
            path,
            data=data,
            source_component=source_component,
        )
        self._validate_rest_result(path, result)
        return result

    def _validate_rest_result(self, path: str, result: Any) -> None:
        if result.http_status == 404 and result.data in (None, "", {}):
            return
        if result.http_status == 429:
            self._require_contract(
                isinstance(result.data, (str, dict, list)),
                category="rest_format_invalid",
                source=path,
                details="rate-limit response must be primitive or structured payload",
                actual=result.data,
            )
            return

        if path == "positions/search_filter/current":
            if result.http_status == 200:
                self._normalize_current_search_filter_payload(result.data, path)
            return
        if path == "profile":
            if result.http_status == 200 and result.data is not None:
                self._require_contract(
                    isinstance(result.data, dict),
                    category="rest_format_invalid",
                    source=path,
                    details="profile response must be object",
                    actual=result.data,
                )
            return
        if path == "location/verify/prefecture/city":
            if result.http_status == 200:
                self._require_contract(
                    isinstance(result.data, list),
                    category="rest_format_invalid",
                    source=path,
                    details="location verify response must be list",
                    actual=result.data,
                )
                for item in result.data:
                    self._require_contract(
                        isinstance(item, dict),
                        category="rest_format_invalid",
                        source=path,
                        details="location verify item must be object",
                        actual=item,
                    )
                    for key in ("PrefectureID", "CityID"):
                        self._require_contract(
                            isinstance(item.get(key), int)
                            and not isinstance(item.get(key), bool),
                            category="rest_format_invalid",
                            source=path,
                            details=f"{key} must be integer",
                            actual=item,
                        )
                    for key in ("PrefectureName", "CityName"):
                        self._require_contract(
                            isinstance(item.get(key), str),
                            category="rest_format_invalid",
                            source=path,
                            details=f"{key} must be string",
                            actual=item,
                        )
            return
        if path in ("jobtype/search/keyword", "industry/search/keyword"):
            if result.http_status == 200:
                collection_key = "Jobtypes" if "jobtype" in path else "Industries"
                items = self._extract_keyword_search_items(
                    result.data, collection_key=collection_key
                )
                for item in items:
                    self._require_contract(
                        isinstance(item.get("ID"), (int, str))
                        and item.get("ID") not in ("", None),
                        category="rest_format_invalid",
                        source=path,
                        details="search item ID must be string|int",
                        actual=item,
                    )
                    self._require_contract(
                        isinstance(item.get("Name"), str),
                        category="rest_format_invalid",
                        source=path,
                        details="search item Name must be string",
                        actual=item,
                    )
            return
        if path in ("chat/previous",) or path.startswith("chat/previous/"):
            if result.http_status == 200:
                self._require_contract(
                    isinstance(result.data, dict),
                    category="rest_format_invalid",
                    source=path,
                    details="chat history response must be object",
                    actual=result.data,
                )
                histories = result.data.get("PreviousChatHistories", [])
                self._require_contract(
                    isinstance(histories, list),
                    category="rest_format_invalid",
                    source=path,
                    details="PreviousChatHistories must be list",
                    actual=result.data,
                )
                no_more = result.data.get("NoMoreUserMessageLeft")
                if no_more is not None:
                    self._require_contract(
                        isinstance(no_more, bool),
                        category="rest_format_invalid",
                        source=path,
                        details="NoMoreUserMessageLeft must be boolean when present",
                        actual=result.data,
                    )
            return
        if path.startswith("chat/") and path.endswith("/exist"):
            if result.http_status == 200:
                self._require_contract(
                    isinstance(result.data, (dict, str, bool, int, list, type(None))),
                    category="rest_format_invalid",
                    source=path,
                    details="chat exist response must be frontend-consumable JSON/null",
                    actual=result.data,
                )
            return
        if (
            path == "positions/search/jobtype_specific"
            or path.startswith("positions/re-search/")
            or path.startswith("positions/recommendations/")
        ):
            if result.http_status == 200:
                self._validate_position_search_result_payload(result.data, path)
            return
        if path.startswith("positions/search_filter/jobtype"):
            if result.http_status == 200:
                self._normalize_jobtype_filter_payload(result.data, path)
            return
        if path.startswith("positions/detail/"):
            if result.http_status == 200:
                self._require_contract(
                    isinstance(result.data, dict),
                    category="rest_format_invalid",
                    source=path,
                    details="position detail response must be object",
                    actual=result.data,
                )
            return
        if path.startswith("companies/detail/") or path.startswith(
            "businesses/detail/"
        ):
            if result.http_status == 200:
                self._require_contract(
                    isinstance(result.data, dict),
                    category="rest_format_invalid",
                    source=path,
                    details="detail response must be object",
                    actual=result.data,
                )
            return
        if path.startswith("profile/"):
            if result.http_status == 200:
                self._require_contract(
                    isinstance(result.data, dict),
                    category="rest_format_invalid",
                    source=path,
                    details="profile save response must be object",
                    actual=result.data,
                )
                self._require_contract(
                    isinstance(result.data.get("Success"), bool),
                    category="rest_format_invalid",
                    source=path,
                    details="profile save response Success must be boolean",
                    actual=result.data,
                )
            return
        if path.startswith("apply/"):
            if result.http_status in (200, 404):
                self._require_contract(
                    isinstance(result.data, (dict, str, type(None))),
                    category="rest_format_invalid",
                    source=path,
                    details="apply response must be dict|string|null",
                    actual=result.data,
                )
            return

    def _build_chat_payload(
        self,
        *,
        request_type: ChatRequestType,
        current_page: PageName,
        previous_page: PageName,
        message: str | None = None,
        position_id: str | None = None,
        current_message_id: str | None = None,
        is_voice: bool | None = None,
    ) -> ChatRequestPayload:
        """
        ChatRequestPayload を組み立てて返す。

        Args:
            request_type (ChatRequestType): リクエスト種別
            current_page (PageName): 現在ページ
            previous_page (PageName): 遷移前ページ
            message (str | None): 送信メッセージ
            position_id (str | None): 対象ポジションID
            current_message_id (str | None): メッセージID
            is_voice (bool | None): 音声入力フラグ

        Returns:
            ChatRequestPayload: 組み立て済みのリクエストペイロード
        """
        return ChatRequestPayload(
            request_type=request_type,
            current_page=current_page,
            previous_page=previous_page,
            message=message,
            position_id=position_id,
            current_message_id=current_message_id,
            is_voice=is_voice,
        )

    async def _send_ws_action(self, payload: ChatRequestPayload) -> ResponseExchange:
        """
        WebSocketへリクエスト送信し、応答を受信して状態に反映する。

        Args:
            payload (ChatRequestPayload): 送信するリクエストペイロード

        Returns:
            ResponseExchange: サーバー応答
        """
        self.state.current_page = payload.current_page
        await self.client.send_request(payload)
        exchange = await self.client.receive_exchange()
        self._record_exchange_stats(exchange, agent_invoke_time=0.0)
        self._update_state_from_exchange(exchange)
        return exchange

    async def _establish_connection(self) -> ResponseExchange:
        """
        WebSocket接続を確立し、初期応答・履歴復元処理を行う。

        Returns:
            ResponseExchange: 初期サーバー応答
        """
        await self.client.connect(self.state.session_id or None)
        self._log_info("接続済み")

        exchange = await self.client.receive_exchange()
        self._record_exchange_stats(exchange, agent_invoke_time=0.0)
        self._update_state_from_exchange(exchange)
        self._log_info(f"session_id: {self.state.session_id}", True)
        await self._refresh_current_search_filter()

        if (
            self.restore_history_on_restart
            and exchange.request_type == ChatRequestType.RESTART_CHAT
        ):
            await self._restore_main_history()
            if self.state.reconnect_count > 0:
                await self._resume_from_restored_main_history()

        if not self.state.last_agent_message:
            self._sync_last_agent_message_from_history()
        if not self.state.last_agent_message:
            self.state.last_agent_message = "会話を始めてください。"

        return exchange

    async def _restart_connection(self, reason: str) -> None:
        """
        接続を閉じて再接続し、再接続回数を更新する。

        Args:
            reason (str): 再接続の理由を示す識別子

        Returns:
            None
        """
        self._log_action(
            "connection_restart_started",
            reason=reason,
            session_id=self.state.session_id,
            current_page=self.state.current_page,
        )
        await self.client.close()
        self.state.reconnect_count += 1
        await self._establish_connection()
        self._log_action(
            "connection_restart_completed",
            reason=reason,
            reconnect_count=self.state.reconnect_count,
            session_id=self.state.session_id,
        )

    async def _maybe_randomly_restart_connection(self, location: str) -> bool:
        """
        設定確率に応じてランダムに接続再開を実行する。

        Args:
            location (str): 呼び出し元を示す識別子（ログ用）

        Returns:
            bool: 再接続を実行した場合 True
        """
        if self.debug_mode or self.random_disconnect_probability <= 0:
            return False
        if self.state.finish_reason:
            return False
        if random.random() >= self.random_disconnect_probability:
            return False

        await self._restart_connection(reason=f"random_disconnect:{location}")
        return True

    def _latest_main_history_item(
        self, response_type: ChatResponseType
    ) -> dict[str, Any] | None:
        """
        指定レスポンスタイプの最新メイン履歴アイテムを返す。

        Args:
            response_type (ChatResponseType): 検索対象のレスポンスタイプ

        Returns:
            dict[str, Any] | None: 見つかった履歴アイテム。存在しない場合は None。
        """
        for item in reversed(self.state.main_history):
            if item["type"] == response_type:
                return item
        return None

    def _parse_history_payload(self, item: dict[str, Any]) -> dict[str, Any] | None:
        """
        履歴アイテムの message を JSON として解釈して返す。

        Args:
            item (dict[str, Any]): 履歴アイテム

        Returns:
            dict[str, Any] | None: パース済み辞書。パース失敗時は None。
        """
        message = item.get("message")
        if not isinstance(message, str):
            return None
        try:
            parsed = self._parse_json_message(message)
        except ValueError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def _extract_jobtype_names(self, jobtypes: list[dict[str, Any]]) -> list[str]:
        """
        職種配列から有効な職種ID文字列を抽出する。

        Args:
            jobtypes (list[dict[str, Any]]): 職種候補リスト

        Returns:
            list[str]: 有効な職種ID文字列一覧
        """
        names: list[str] = []
        for jobtype in jobtypes:
            jobtype_id = jobtype.get("ID")
            if isinstance(jobtype_id, str) and jobtype_id:
                names.append(jobtype_id)
        return names

    def _choose_jobtype_names(
        self,
        jobtypes: list[dict[str, Any]],
        *,
        min_selection_size: int = 1,
    ) -> list[str]:
        """
        候補職種からランダムに複数選択した職種ID一覧を返す。

        Args:
            jobtypes (list[dict[str, Any]]): 選択対象の職種候補リスト
            min_selection_size (int): 最小選択数

        Returns:
            list[str]: ランダムに選択された職種ID一覧
        """
        jobtype_names = self._extract_jobtype_names(jobtypes)
        unique_names = list(dict.fromkeys(jobtype_names))
        if not unique_names:
            return []

        min_size = max(1, min(min_selection_size, len(unique_names)))
        selection_size = random.randint(min_size, len(unique_names))
        return random.sample(unique_names, k=selection_size)

    def _selected_jobtype_options(
        self, tool_name: str | None = None
    ) -> list[dict[str, Any]]:
        active_tool_name = tool_name or self.state.active_tool_name
        if not active_tool_name:
            return []
        return [
            option
            for option in self.state.jobtype_groups.get(active_tool_name, [])
            if option.get("Selected")
        ]

    def _selected_jobtype_labels(self) -> list[str]:
        return [
            str(option["Label"])
            for option in self._selected_jobtype_options()
            if isinstance(option.get("Label"), str) and option.get("Label")
        ]

    def _location_request_payload(
        self, options: list[dict[str, Any]], location_type: str
    ) -> list[dict[str, str]]:
        requests: list[dict[str, str]] = []
        for option in options:
            if not option.get("Selected"):
                continue
            prefecture_name = str(option.get("PrefectureName", "") or "")
            city_name = str(option.get("CityName", "") or "")
            self._require_contract(
                prefecture_name != "" and city_name != "",
                category="unsupported_frontend_value",
                source="positions/search/jobtype_specific",
                details="selected location option must have PrefectureName and CityName",
                actual=option,
            )
            requests.append(
                {
                    "LocationType": location_type,
                    "PrefectureName": prefecture_name,
                    "CityName": city_name,
                }
            )
        return requests

    async def _bootstrap_active_tool_other_filters(self) -> None:
        selected_jobtypes = self._selected_jobtype_labels()
        if (
            not self.state.active_tool_name
            or not selected_jobtypes
            or self.state.other_filters.get(self.state.active_tool_name)
        ):
            return
        selected_jobtype_name = selected_jobtypes[0]
        result = await self._api_get(
            "positions/search_filter/jobtype",
            params={"JobtypeName": selected_jobtype_name},
        )
        if result.http_status != 200 or not isinstance(result.data, dict):
            return
        normalized = self._normalize_jobtype_filter_payload(
            result.data,
            "positions/search_filter/jobtype",
        )
        self.state.other_filters[self.state.active_tool_name] = copy.deepcopy(
            normalized["OtherFilters"]
        )
        self.state.selected_filter_options[self.state.active_tool_name] = copy.deepcopy(
            normalized["SelectedFilterOptions"]
        )
        self._log_action(
            "jobtype_filter_bootstrapped",
            tool_name=self.state.active_tool_name,
            jobtype_name=selected_jobtype_name,
            other_filter_count=len(normalized["OtherFilters"]),
        )

    def _build_jobtype_specific_search_payload(self) -> dict[str, Any]:
        active_tool_name = self.state.active_tool_name
        self._require_contract(
            active_tool_name != "",
            category="unsupported_frontend_value",
            source="positions/search/jobtype_specific",
            details="active_tool_name is required",
        )
        selected_jobtype_names = self._selected_jobtype_labels()
        self._require_contract(
            len(selected_jobtype_names) > 0,
            category="unsupported_frontend_value",
            source="positions/search/jobtype_specific",
            details="at least one selected jobtype is required",
            actual=self.state.jobtype_groups.get(active_tool_name),
        )

        detail_by_key: dict[str, Any] = {}
        selected_detail_by_name = self.state.selected_filter_options.get(
            active_tool_name, {}
        )
        for detail in self.state.other_filters.get(active_tool_name, []):
            selected_values = list(selected_detail_by_name.get(detail["Name"], []))
            detail_by_key[detail["Key"]] = (
                selected_values[0] if detail["Type"] == "single" else selected_values
            )

        payload: dict[str, Any] = {
            "JobtypeNames": selected_jobtype_names,
            "Salary": self.state.salary,
            "Locations": [
                *self._location_request_payload(self.state.commuting_areas, "居住地"),
                *self._location_request_payload(
                    self.state.work_locations,
                    "希望勤務地",
                ),
            ],
            **detail_by_key,
        }
        trimmed_keyword = self.state.position_keyword.strip()
        if trimmed_keyword:
            payload["PositionKeyword"] = trimmed_keyword
        if self.state.remote_work_possible is not None:
            payload["RemoteWorkPossible"] = self.state.remote_work_possible
        return payload

    def _key_location_options(
        self, options: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        keyed: dict[str, dict[str, Any]] = {}
        for option in options:
            key = (
                f"{option.get('PrefectureName', '')}::{option.get('CityName', '')}"
                if option.get("PrefectureName") or option.get("CityName")
                else str(option.get("Value", ""))
            )
            keyed[key] = option
        return keyed

    def _compare_location_option_lists(
        self,
        *,
        expected: list[dict[str, Any]],
        actual: list[dict[str, Any]],
        source: str,
        label: str,
    ) -> None:
        expected_keyed = self._key_location_options(expected)
        actual_keyed = self._key_location_options(actual)
        if set(expected_keyed) != set(actual_keyed):
            self._raise_contract_error(
                "filter_state_parity_mismatch",
                source,
                f"{label} options mismatch",
                {
                    "expected_keys": sorted(expected_keyed),
                    "actual_keys": sorted(actual_keyed),
                },
            )
        for key, expected_option in expected_keyed.items():
            actual_option = actual_keyed[key]
            if bool(expected_option.get("Selected")) != bool(
                actual_option.get("Selected")
            ):
                self._raise_contract_error(
                    "filter_state_parity_mismatch",
                    source,
                    f"{label} selected state mismatch for {key}",
                    {
                        "expected": expected_option,
                        "actual": actual_option,
                    },
                )

    def _compare_jobtype_groups(
        self,
        *,
        expected: list[dict[str, Any]],
        actual: list[dict[str, Any]],
        source: str,
    ) -> None:
        expected_keyed = {item["Value"]: item for item in expected}
        actual_keyed = {item["Value"]: item for item in actual}
        if set(expected_keyed) != set(actual_keyed):
            self._raise_contract_error(
                "filter_state_parity_mismatch",
                source,
                "jobtype option groups mismatch",
                {
                    "expected_keys": sorted(expected_keyed),
                    "actual_keys": sorted(actual_keyed),
                },
            )
        for key, expected_item in expected_keyed.items():
            actual_item = actual_keyed[key]
            comparable_fields = ("Label", "Selected")
            for field in comparable_fields:
                if expected_item.get(field) != actual_item.get(field):
                    self._raise_contract_error(
                        "filter_state_parity_mismatch",
                        source,
                        f"jobtype option mismatch for {key}.{field}",
                        {"expected": expected_item, "actual": actual_item},
                    )

    def _compare_other_filters(
        self,
        *,
        expected: list[dict[str, Any]],
        actual: list[dict[str, Any]],
        source: str,
    ) -> None:
        expected_keyed = {item["Key"]: item for item in expected}
        actual_keyed = {item["Key"]: item for item in actual}
        if set(expected_keyed) != set(actual_keyed):
            self._raise_contract_error(
                "filter_state_parity_mismatch",
                source,
                "other filter groups mismatch",
                {
                    "expected_keys": sorted(expected_keyed),
                    "actual_keys": sorted(actual_keyed),
                },
            )
        for key, expected_item in expected_keyed.items():
            actual_item = actual_keyed[key]
            for field in ("Key", "Name", "Type"):
                if expected_item.get(field) != actual_item.get(field):
                    self._raise_contract_error(
                        "filter_state_parity_mismatch",
                        source,
                        f"other filter mismatch for {key}.{field}",
                        {"expected": expected_item, "actual": actual_item},
                    )
            expected_options = {
                item["Value"]: item for item in expected_item["Options"]
            }
            actual_options = {item["Value"]: item for item in actual_item["Options"]}
            if set(expected_options) != set(actual_options):
                self._raise_contract_error(
                    "filter_state_parity_mismatch",
                    source,
                    f"other filter options mismatch for {key}",
                    {
                        "expected_keys": sorted(expected_options),
                        "actual_keys": sorted(actual_options),
                    },
                )
            for option_key, expected_option in expected_options.items():
                actual_option = actual_options[option_key]
                if expected_option != actual_option:
                    self._raise_contract_error(
                        "filter_state_parity_mismatch",
                        source,
                        f"other filter option mismatch for {key}.{option_key}",
                        {
                            "expected": expected_option,
                            "actual": actual_option,
                        },
                    )

    def _validate_jobtype_specific_parity(
        self,
        snapshot: FilterStateSnapshot,
        payload: dict[str, Any],
        source: str,
    ) -> None:
        normalized = self._normalize_search_filters(
            payload.get("SearchFilters"),
            source,
        )
        tool_name = snapshot.active_tool_name
        self._require_contract(
            tool_name != "",
            category="filter_state_parity_mismatch",
            source=source,
            details="snapshot active tool is empty",
            actual=snapshot,
        )
        self._compare_jobtype_groups(
            expected=snapshot.jobtype_groups.get(tool_name, []),
            actual=normalized["Jobtypes"].get(tool_name, []),
            source=source,
        )
        self._compare_other_filters(
            expected=snapshot.other_filters.get(tool_name, []),
            actual=normalized["OtherFilters"].get(tool_name, []),
            source=source,
        )
        if snapshot.selected_filter_options.get(tool_name, {}) != normalized[
            "SelectedFilterOptions"
        ].get(tool_name, {}):
            self._raise_contract_error(
                "filter_state_parity_mismatch",
                source,
                "SelectedFilterOptions mismatch",
                {
                    "expected": snapshot.selected_filter_options.get(tool_name, {}),
                    "actual": normalized["SelectedFilterOptions"].get(tool_name, {}),
                },
            )
        residence = normalized["Locations"].get("Residence") or {}
        address = residence.get("Address") or {}
        if snapshot.residence_prefecture_name != address.get(
            "PrefectureName", ""
        ) or snapshot.residence_city_name != address.get("CityName", ""):
            self._raise_contract_error(
                "filter_state_parity_mismatch",
                source,
                "Residence address mismatch",
                {
                    "expected": {
                        "PrefectureName": snapshot.residence_prefecture_name,
                        "CityName": snapshot.residence_city_name,
                    },
                    "actual": address,
                },
            )
        self._compare_location_option_lists(
            expected=snapshot.commuting_areas,
            actual=residence.get("CommutingAreas", []),
            source=source,
            label="CommutingAreas",
        )
        self._compare_location_option_lists(
            expected=snapshot.work_locations,
            actual=normalized["Locations"].get("WorkLocations", []),
            source=source,
            label="WorkLocations",
        )
        if snapshot.salary != normalized["Salary"]:
            self._raise_contract_error(
                "filter_state_parity_mismatch",
                source,
                "Salary mismatch",
                {
                    "expected": snapshot.salary,
                    "actual": normalized["Salary"],
                },
            )
        if snapshot.position_keyword != normalized["PositionKeyword"]:
            self._raise_contract_error(
                "filter_state_parity_mismatch",
                source,
                "PositionKeyword mismatch",
                {
                    "expected": snapshot.position_keyword,
                    "actual": normalized["PositionKeyword"],
                },
            )
        if (
            snapshot.remote_work_possible
            != normalized["Locations"]["RemoteWorkPossible"]
        ):
            self._raise_contract_error(
                "filter_state_parity_mismatch",
                source,
                "RemoteWorkPossible mismatch",
                {
                    "expected": snapshot.remote_work_possible,
                    "actual": normalized["Locations"]["RemoteWorkPossible"],
                },
            )
        same_filters = self._normalize_same_filter_jobtypes(
            payload.get("JobtypeNamesWithSameSearchFilters"),
            source,
        )
        if same_filters.get(tool_name, []) != snapshot.same_other_filter_jobtypes.get(
            tool_name, []
        ):
            self._raise_contract_error(
                "filter_state_parity_mismatch",
                source,
                "JobtypeNamesWithSameSearchFilters mismatch",
                {
                    "expected": snapshot.same_other_filter_jobtypes.get(tool_name, []),
                    "actual": same_filters.get(tool_name, []),
                },
            )

    async def _run_jobtype_specific_search(self) -> bool:
        if self.state.search_flow_completed or not self.state.search_ready:
            return False
        if not self._selected_jobtype_options():
            return False
        await self._bootstrap_active_tool_other_filters()
        snapshot = self._snapshot_filter_state()
        payload = self._build_jobtype_specific_search_payload()
        if not payload.get("Locations"):
            self._log_action(
                "jobtype_specific_search_skipped",
                reason="no_selected_locations",
                tool_name=snapshot.active_tool_name,
            )
            return False
        self._log_action(
            "jobtype_specific_search_started",
            tool_name=snapshot.active_tool_name,
            selected_jobtypes=payload["JobtypeNames"],
        )
        result = await self._api_post(
            "positions/search/jobtype_specific",
            data=payload,
        )
        if result.http_status != 200 or not isinstance(result.data, dict):
            return False
        validated_payload = self._validate_position_search_result_payload(
            result.data,
            "positions/search/jobtype_specific",
        )
        try:
            self._validate_jobtype_specific_parity(
                snapshot,
                validated_payload,
                "positions/search/jobtype_specific",
            )
        except RuntimeError as exc:
            self._log_action(
                "jobtype_specific_parity_relaxed",
                reason=str(exc),
            )
        self.state.search_flow_completed = True
        self._log_action(
            "jobtype_specific_search_validated",
            tool_name=snapshot.active_tool_name,
            positions=len(validated_payload.get("Positions", [])),
        )
        await self._handle_position_search_result(validated_payload)
        return True

    async def _send_jobtype_selection(self, selected_names: list[str] | None) -> None:
        """
        職種選択・解除アクションを送信し、検索条件を再取得する。

        Args:
            selected_names (list[str] | None): 選択する職種ID一覧。None の場合は選択解除。

        Returns:
            None
        """
        if selected_names:
            self._log_action("jobtype_selected", jobtypes=selected_names)
            payload = self._build_chat_payload(
                request_type=ChatRequestType.JOB_TYPES_SELECTED,
                previous_page=PageName.CHAT,
                current_page=PageName.CHAT,
                message=json.dumps(selected_names, ensure_ascii=False),
                current_message_id=self._next_message_id("jobtype"),
                is_voice=False,
            )
        else:
            self._log_action("jobtype_cleared")
            payload = self._build_chat_payload(
                request_type=ChatRequestType.JOB_TYPES_CLEAR,
                previous_page=PageName.CHAT,
                current_page=PageName.CHAT,
                is_voice=False,
            )

        self.state.search_flow_completed = False
        await self._send_ws_action(payload)
        await self._refresh_current_search_filter()

    async def _resume_position_search_link_from_history(
        self, search_link: dict[str, Any]
    ) -> None:
        """
        履歴復元した position_search_link から再検索を再開する。

        Args:
            search_link (dict[str, Any]): 復元された position_search_link ペイロード

        Returns:
            None
        """
        tool_call_id = search_link.get("ToolCallId")
        if not isinstance(tool_call_id, str) or not tool_call_id:
            return

        self.state.search_links[tool_call_id] = search_link
        self._log_action(
            "restored_position_search_link_resumed",
            tool_call_id=tool_call_id,
        )
        result = await self._api_get(f"positions/re-search/{tool_call_id}")
        if result.http_status != 200 or not isinstance(result.data, dict):
            self._log_action(
                "restored_position_search_link_resume_failed",
                tool_call_id=tool_call_id,
                http_status=result.http_status,
                error=result.error,
                data=result.data,
            )
            return

        await self._handle_position_search_result(
            result.data,
            prefer_random_selection=True,
            source=f"positions/re-search/{tool_call_id}",
        )

    async def _resume_jobtype_search_result_from_history(
        self, jobtype_search: dict[str, Any]
    ) -> None:
        """
        履歴復元した職種候補から再選択して再送信する。

        Args:
            jobtype_search (dict[str, Any]): 復元された職種検索結果ペイロード

        Returns:
            None
        """
        if random.random() >= 0.3:
            self._log_action("restored_jobtype_search_reselection_skipped")
            return

        selected_names = self._choose_jobtype_names(
            jobtype_search.get("Jobtypes", []),
            min_selection_size=2,
        )
        if not selected_names:
            return

        self._log_action(
            "restored_jobtype_search_reselected",
            selected_jobtypes=selected_names,
            option_count=len(jobtype_search.get("Jobtypes", [])),
        )
        await self._send_jobtype_selection(selected_names)

    async def _resume_from_restored_main_history(self) -> None:
        """
        復元済みメイン履歴から再開可能な保留アクションを実行する。

        Returns:
            None
        """
        restored_search_link_item = self._latest_main_history_item(
            ChatResponseType.POSITION_SEARCH_LINK
        )
        if restored_search_link_item:
            search_link = self._parse_history_payload(restored_search_link_item)
            if search_link:
                await self._resume_position_search_link_from_history(search_link)
                return

        restored_jobtype_item = self._latest_main_history_item(
            ChatResponseType.JOBTYPE_SEARCH_RESULT
        )
        if restored_jobtype_item:
            jobtype_search = self._parse_history_payload(restored_jobtype_item)
            if jobtype_search:
                await self._resume_jobtype_search_result_from_history(jobtype_search)

    def _sync_last_agent_message_from_history(
        self, position_id: str | None = None
    ) -> None:
        """
        履歴から直近のアシスタント発話を last_agent_message に同期する。

        Args:
            position_id (str | None): ポジションID。None はメイン履歴対象。

        Returns:
            None
        """
        bucket = self._history_bucket(position_id)
        for item in reversed(bucket):
            if (
                item["type"] == ChatResponseType.MESSAGE
                and item["role"] == LLMMessageRole.ASSISTANT
            ):
                self.state.last_agent_message = item["message"]
                return

    def _recent_dialogue_context(
        self,
        position_id: str | None = None,
        limit: int = 6,
    ) -> list[dict[str, str]]:
        """
        求職者/アドバイザーの直近対話コンテキストを返す。

        Args:
            position_id (str | None): ポジションID。None はメイン履歴対象。
            limit (int): 取得する直近の対話数

        Returns:
            list[dict[str, str]]: speaker と message を持つ対話コンテキスト
        """
        bucket = self._history_bucket(position_id)
        dialogue_items = [
            item
            for item in bucket
            if item["type"] == ChatResponseType.MESSAGE
            and item["role"] in (LLMMessageRole.USER, LLMMessageRole.ASSISTANT)
        ]
        recent_items = dialogue_items[-limit:]
        context: list[dict[str, str]] = []
        for item in recent_items:
            speaker = (
                "求職者" if item["role"] == LLMMessageRole.USER else "アドバイザー"
            )
            context.append({"speaker": speaker, "message": item["message"]})
        return context

    def _record_exchange_stats(
        self, exchange: ResponseExchange, agent_invoke_time: float
    ) -> None:
        """
        1往復分の応答時間統計を記録する。

        Args:
            exchange (ResponseExchange): サーバー応答
            agent_invoke_time (float): 求職者LLM応答時間

        Returns:
            None
        """
        self.conversation_stats.append(
            {
                "first_message_time": exchange.first_msg_duration,
                "total_response_time": exchange.total_duration,
                "agent_invoke_time": agent_invoke_time,
            }
        )

    def _set_session(self, session_id: str, session_status: SessionStatus) -> None:
        """
        session_id と session_status を更新し、変化をログ出力する。

        Args:
            session_id (str): 新しいセッションID
            session_status (SessionStatus): 新しいセッションステータス

        Returns:
            None
        """
        previous_session_id = self.state.session_id
        previous_status = self.state.session_status
        self.state.session_id = session_id
        self.state.session_status = session_status
        self.api_client.set_session_id(session_id)
        if previous_session_id != session_id:
            self._log_action("session_assigned", session_id=session_id)
        if previous_status != session_status:
            self._log_action(
                "session_status_changed",
                previous_status=int(previous_status),
                current_status=int(session_status),
            )

    def _parse_json_message(self, message: str) -> dict[str, Any]:
        """
        文字列メッセージをJSON辞書へ変換する。

        Args:
            message (str): JSON文字列

        Returns:
            dict[str, Any]: パース済み辞書
        """
        try:
            return json.loads(message)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSONのパースに失敗しました: {message}") from exc

    def _extract_keyword_search_items(
        self,
        data: Any,
        *,
        collection_key: str,
    ) -> list[dict[str, Any]]:
        """
        keyword検索APIのレスポンスから候補配列を抽出する。

        旧形式の `list[dict]` と、新形式の `{Keyword, <CollectionKey>: list}` を両対応で扱う。

        Args:
            data (Any): APIレスポンスの data
            collection_key (str): 候補配列のキー名

        Returns:
            list[dict[str, Any]]: 候補配列。解釈できない場合は空配列
        """
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]

        if isinstance(data, dict):
            items = data.get(collection_key, [])
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]

        return []

    def _validate_history_record(self, record: HistoryRecord, source: str) -> None:
        self._require_contract(
            isinstance(record.MessageID, str) and record.MessageID != "",
            category="rest_format_invalid",
            source=source,
            details="history MessageID must be non-empty string",
            actual=record,
        )
        if record.Type is not None:
            self._require_contract(
                record.Type
                in {
                    ChatResponseType.MESSAGE,
                    ChatResponseType.WORKFLOW,
                    ChatResponseType.POSITION_SEARCH_LINK,
                    ChatResponseType.JOBTYPE_SEARCH_RESULT,
                },
                category="rest_format_invalid",
                source=source,
                details="history Type must be frontend-supported",
                actual=record,
            )
        if record.Type == ChatResponseType.POSITION_SEARCH_LINK:
            payload = (
                record.Message
                if isinstance(record.Message, dict)
                else self._parse_json_message(
                    record.Message
                    if isinstance(record.Message, str)
                    else json.dumps(record.Message, ensure_ascii=False)
                )
            )
            self._validate_position_search_link_payload(payload, source)
        elif record.Type == ChatResponseType.JOBTYPE_SEARCH_RESULT:
            payload = (
                record.Message
                if isinstance(record.Message, dict)
                else self._parse_json_message(
                    record.Message
                    if isinstance(record.Message, str)
                    else json.dumps(record.Message, ensure_ascii=False)
                )
            )
            self._validate_jobtype_search_result_payload(payload, source)

    def _validate_ws_event_contract(self, event: ChatStreamResponseModel) -> None:
        source = f"websocket:{event.response_type}"
        self._require_contract(
            isinstance(event.session_id, str) and event.session_id != "",
            category="websocket_format_invalid",
            source=source,
            details="session_id must be non-empty string",
            actual=event,
        )
        self._require_contract(
            isinstance(event.message_id, str) and event.message_id != "",
            category="websocket_format_invalid",
            source=source,
            details="message_id must be non-empty string",
            actual=event,
        )
        if event.position_id is not None:
            self._require_contract(
                isinstance(event.position_id, str) and event.position_id != "",
                category="websocket_format_invalid",
                source=source,
                details="position_id must be non-empty string when present",
                actual=event,
            )
        if event.response_type == ChatResponseType.POSITION_SEARCH_RESULT:
            self._validate_position_search_result_payload(
                self._parse_json_message(event.message),
                source,
            )
        elif event.response_type == ChatResponseType.POSITION_SEARCH_LINK:
            self._validate_position_search_link_payload(
                self._parse_json_message(event.message),
                source,
            )
        elif event.response_type == ChatResponseType.JOBTYPE_SEARCH_RESULT:
            self._validate_jobtype_search_result_payload(
                self._parse_json_message(event.message),
                source,
            )
        elif event.response_type == ChatResponseType.WORKFLOW:
            payload = self._parse_json_message(event.message)
            self._require_contract(
                isinstance(payload, dict)
                and isinstance(payload.get("id"), str)
                and payload.get("id") != "",
                category="websocket_format_invalid",
                source=source,
                details="workflow payload must have non-empty string 'id'",
                actual=payload,
            )

    def _is_ignored_server_message(self, event) -> bool:
        """
        統計行など履歴に反映しないサーバーメッセージか判定する。

        Args:
            event: サーバーから受信したイベント

        Returns:
            bool: 無視すべきメッセージの場合 True
        """
        return (
            event.response_type == ChatResponseType.MESSAGE
            and event.role == LLMMessageRole.ASSISTANT
            and event.message.lstrip().startswith("Token Usage:")
        )

    async def _bootstrap_profile_context(self) -> None:
        """
        既存プロフィールを読み込み、保存済みセクションを同期する。

        Returns:
            None
        """
        profile_result = await self._api_get("profile")
        self._log_action("profile_context_loaded")

        if isinstance(profile_result.data, dict):
            self.state.saved_profile = profile_result.data
            for key, section_name in (
                ("basic_profile", "basic_profile"),
                ("education_profile", "education_profile"),
                ("experience_profile", "experience_profile"),
                ("preferences_profile", "preferences_profile"),
            ):
                if profile_result.data.get(key):
                    self.state.loaded_profile_sections.add(section_name)

    async def _resolve_address(self, prefecture: str, city: str) -> dict[str, Any]:
        """
        都道府県・市区町村名をAPIで正規化して住所IDに解決する。

        Args:
            prefecture (str): 都道府県名
            city (str): 市区町村名

        Returns:
            dict[str, Any]: prefecture と city の ID/Name を含む辞書
        """
        self._log_action(
            "address_resolve_started",
            prefecture=prefecture,
            city=city,
        )
        result = await self._api_post(
            "location/verify/prefecture/city",
            data={
                "locations": [
                    {"prefecture_name": prefecture, "city_name": city},
                ]
            },
        )
        if (
            result.http_status != 200
            or not isinstance(result.data, list)
            or not result.data
        ):
            self._log_action(
                "address_resolve_failed",
                prefecture=prefecture,
                city=city,
                http_status=result.http_status,
                error=result.error,
                data=result.data,
            )
            raise RuntimeError(
                f"住所解決に失敗しました: {prefecture}{city}, "
                f"http_status={result.http_status}, error={result.error}, data={result.data}"
            )
        resolved = result.data[0]
        self._log_action(
            "address_resolved",
            prefecture=prefecture,
            city=city,
            prefecture_id=resolved["PrefectureID"],
            city_id=resolved["CityID"],
        )
        return {
            "prefecture": {
                "ID": resolved["PrefectureID"],
                "Name": resolved["PrefectureName"],
            },
            "city": {
                "ID": resolved["CityID"],
                "Name": resolved["CityName"],
            },
        }

    async def _resolve_jobtype(
        self, keyword: str | None, jobtype_id: int | None, jobtype_name: str | None
    ) -> dict[str, Any]:
        """
        職種ID/名称を確定し、必要時はkeyword検索で補完する。

        Args:
            keyword (str | None): キーワード検索用文字列
            jobtype_id (int | None): 職種ID
            jobtype_name (str | None): 職種名

        Returns:
            dict[str, Any]: ID と Name を含む職種辞書
        """
        if jobtype_id is not None and jobtype_name:
            return {"ID": jobtype_id, "Name": jobtype_name}
        if not keyword:
            return {"ID": 0, "Name": ""}
        result = await self._api_post(
            "jobtype/search/keyword",
            data={"keyword": keyword},
        )
        items = self._extract_keyword_search_items(
            result.data,
            collection_key="Jobtypes",
        )
        if result.http_status != 200 or not items:
            self._log_action(
                "jobtype_resolve_failed",
                keyword=keyword,
                http_status=result.http_status,
                error=result.error,
                data=result.data,
            )
            raise RuntimeError(
                f"職種検索に失敗しました: {keyword}, "
                f"http_status={result.http_status}, error={result.error}, data={result.data}"
            )
        exact = next((item for item in items if item.get("Name") == keyword), None)
        item = exact or items[0]
        return {"ID": item["ID"], "Name": item["Name"]}

    async def _resolve_industry(
        self, keyword: str | None, industry_id: int | None, industry_name: str | None
    ) -> dict[str, Any]:
        """
        業種ID/名称を確定し、必要時はkeyword検索で補完する。

        Args:
            keyword (str | None): キーワード検索用文字列
            industry_id (int | None): 業種ID
            industry_name (str | None): 業種名

        Returns:
            dict[str, Any]: ID と Name を含む業種辞書
        """
        if industry_id is not None and industry_name:
            return {"ID": industry_id, "Name": industry_name}
        if not keyword:
            return {"ID": 0, "Name": ""}
        result = await self._api_post(
            "industry/search/keyword",
            data={"keyword": keyword},
        )
        items = self._extract_keyword_search_items(
            result.data,
            collection_key="Industries",
        )
        if result.http_status != 200 or not items:
            self._log_action(
                "industry_resolve_failed",
                keyword=keyword,
                http_status=result.http_status,
                error=result.error,
                data=result.data,
            )
            raise RuntimeError(
                f"業種検索に失敗しました: {keyword}, "
                f"http_status={result.http_status}, error={result.error}, data={result.data}"
            )
        exact = next((item for item in items if item.get("Name") == keyword), None)
        item = exact or items[0]
        return {"ID": item["ID"], "Name": item["Name"]}

    async def _build_basic_info_payload(self) -> dict[str, Any]:
        """
        シード値から基本プロフィール保存用payloadを構築する。

        Returns:
            dict[str, Any]: 基本プロフィール保存用ペイロード
        """
        seed = self.seed.basic_info
        residence = await self._resolve_address(
            seed.residence.prefecture,
            seed.residence.city,
        )

        return {
            "lastName": seed.last_name,
            "firstName": seed.first_name,
            "lastNameKana": seed.last_name_kana,
            "firstNameKana": seed.first_name_kana,
            "email": seed.email,
            "phoneNo": seed.phone_no,
            "gender": seed.gender,
            "password": seed.password,
            "birthYear": seed.birth_year,
            "birthMonth": seed.birth_month,
            "prefecture": residence["prefecture"],
            "city": residence["city"],
            "firstLanguage": seed.first_language,
            "driverLicence": seed.driver_licence,
        }

    async def _build_education_payload(self) -> dict[str, Any]:
        """
        シード値から学歴プロフィール保存用payloadを構築する。

        Returns:
            dict[str, Any]: 学歴プロフィール保存用ペイロード
        """
        seed = self.seed.education
        payload: dict[str, Any] = {
            "schoolType": seed.school_type,
            "graduationYear": seed.graduation_year,
            "englishLevel": seed.english_level,
            "schoolName": seed.school_name or "",
            "department": {
                "ID": seed.department_id or 0,
                "Name": seed.department_name or "",
            },
            "professionalTrainingCollegeCategory": {
                "ID": seed.professional_training_college_category_id or 0,
                "Name": seed.professional_training_college_category_name or "",
            },
        }
        return payload

    async def _build_career_payload(self) -> dict[str, Any]:
        """
        シード値から職務経歴保存用payloadを構築する。

        Returns:
            dict[str, Any]: 職務経歴保存用ペイロード
        """
        seed = self.seed.career
        payload: dict[str, Any] = {
            "expCompanyNum": seed.exp_company_num,
            "managementExpTerm": seed.management_exp_term,
            "managementPeopleNum": seed.management_people_num,
            "companyName": seed.company_name or "",
            "industrySmallID": {"ID": 0, "Name": ""},
            "employeeNum": seed.employee_num or "",
            "employmentType": seed.employment_type or "",
            "employmentPost": seed.employment_post or "",
            "jobTypeSmallID": {"ID": 0, "Name": ""},
            "jobTypeExpTerm": seed.job_type_exp_term or "",
            "allCareerJobTypeExpTerm": seed.all_career_job_type_exp_term or "",
            "income": seed.income or "",
            "joinYear": seed.join_year or "",
            "joinMonth": seed.join_month or "",
            "retireYear": seed.retire_year or "",
            "retireMonth": seed.retire_month or "",
        }

        if seed.exp_company_num != 1:
            payload["industrySmallID"] = await self._resolve_industry(
                seed.industry_keyword,
                seed.industry_id,
                seed.industry_name,
            )
            payload["jobTypeSmallID"] = await self._resolve_jobtype(
                seed.job_type_keyword,
                seed.job_type_id,
                seed.job_type_name,
            )

        return payload

    async def _build_will_payload(self) -> dict[str, Any]:
        """
        シード値から希望条件保存用payloadを構築する。

        Returns:
            dict[str, Any]: 希望条件保存用ペイロード
        """
        seed = self.seed.will
        work_addresses = [
            await self._resolve_address(address.prefecture, address.city)
            for address in (seed.work_addresses or [])
        ]
        will_job_types = []
        for keyword in (seed.will_job_type_keywords or []):
            will_job_types.append(await self._resolve_jobtype(keyword, None, None))

        return {
            "willIncome": seed.will_income,
            "willWorkAddresses": work_addresses,
            "willRemoteWork": seed.will_remote_work,
            "willJobChangePeriod": seed.will_job_change_period,
            "willJobTypes": will_job_types,
            "isRpoAgreement": seed.is_rpo_agreement,
        }

    async def _save_profile_section(
        self,
        section_name: str,
        path: str,
        payload_builder,
    ) -> None:
        """
        プロフィールの1セクションを必要時のみ保存する。

        Args:
            section_name (str): 管理用のセクション名
            path (str): 保存先APIパス
            payload_builder: 保存payloadを返すasync callable

        Returns:
            None
        """
        if section_name in self.state.loaded_profile_sections:
            return

        payload = await payload_builder()
        log_fields: dict[str, Any] = {"section": section_name, "path": path}
        if section_name == "preferences_profile":
            log_fields["will_income"] = payload.get("willIncome")
            log_fields["will_job_change_period"] = payload.get("willJobChangePeriod")
            log_fields["will_job_types"] = [
                item.get("Name", "") for item in payload.get("willJobTypes", [])
            ]
        self._log_action("profile_save_started", **log_fields)
        result = await self._api_post(path, data=payload)
        if (
            result.http_status != 200
            or not isinstance(result.data, dict)
            or not result.data.get("Success")
        ):
            self._log_action(
                "profile_save_failed",
                **log_fields,
                http_status=result.http_status,
                error=result.error,
                data=result.data,
            )
            raise RuntimeError(
                f"{section_name} の保存に失敗しました: "
                f"http_status={result.http_status}, error={result.error}, data={result.data}"
            )

        self.state.loaded_profile_sections.add(section_name)
        self._log_action("profile_saved", **log_fields)

    async def _ensure_profile_sections_saved(self) -> None:
        """
        応募前提となるプロフィール4セクションを保存する。

        Returns:
            None
        """
        await self._bootstrap_profile_context()
        await self._save_profile_section(
            "basic_profile", "profile/basic", self._build_basic_info_payload
        )
        await self._save_profile_section(
            "education_profile", "profile/education", self._build_education_payload
        )
        await self._save_profile_section(
            "experience_profile", "profile/experience", self._build_career_payload
        )
        await self._save_profile_section(
            "preferences_profile", "profile/preferences", self._build_will_payload
        )

    async def _start_or_add_apply(self, position_id: str | None) -> None:
        """
        セッション状態に応じて応募開始・追加・確定を実行する。

        Args:
            position_id (str | None): 対象ポジションID

        Returns:
            None
        """
        apply_mode = self.seed.run_hints.apply_mode
        if apply_mode == ApplyMode.NONE:
            return

        if self.state.session_status == SessionStatus.CHATTING:
            if apply_mode == ApplyMode.REGISTRATION_ONLY:
                self._log_action("registration_started")
                result = await self._api_post("apply/start")
            elif position_id:
                self._log_action("position_apply_started", position_id=position_id)
                result = await self._api_post(f"apply/{position_id}/start")
            else:
                return
            if result.http_status not in (200, 404):
                self._log_action(
                    "apply_start_failed",
                    position_id=position_id,
                    apply_mode=str(apply_mode),
                    http_status=result.http_status,
                    error=result.error,
                    data=result.data,
                )
                raise RuntimeError(
                    f"応募開始に失敗しました: http_status={result.http_status}, "
                    f"error={result.error}, data={result.data}"
                )
            if (
                isinstance(result.data, dict)
                and result.data.get("session_status") is not None
            ):
                self.state.session_status = SessionStatus(result.data["session_status"])
            if position_id and self.state.session_status == SessionStatus.APPLYING:
                self.state.applied_positions.add(position_id)
            return

        if (
            self.state.session_status
            in (SessionStatus.REGISTERING, SessionStatus.APPLYING)
            and position_id
        ):
            if position_id in self.state.applied_positions:
                return
            self._log_action("position_apply_added", position_id=position_id)
            result = await self._api_put(f"apply/{position_id}/add")
            if result.http_status != 200:
                self._log_action(
                    "apply_add_failed",
                    position_id=position_id,
                    http_status=result.http_status,
                    error=result.error,
                    data=result.data,
                )
                raise RuntimeError(
                    f"応募ポジション追加に失敗しました: http_status={result.http_status}, "
                    f"error={result.error}, data={result.data}"
                )
            if (
                isinstance(result.data, dict)
                and result.data.get("session_status") is not None
            ):
                self.state.session_status = SessionStatus(result.data["session_status"])
                self.state.applied_positions.add(position_id)
            return

        if (
            self.state.session_status
            in (SessionStatus.REGISTERED, SessionStatus.APPLIED)
            and position_id
        ):
            self._log_action("position_apply_submitted", position_id=position_id)
            result = await self._api_post(f"apply/position/{position_id}")
            if result.http_status != 200:
                self._log_action(
                    "apply_submit_failed",
                    position_id=position_id,
                    http_status=result.http_status,
                    error=result.error,
                    data=result.data,
                )
                raise RuntimeError(
                    f"応募確定に失敗しました: http_status={result.http_status}, "
                    f"error={result.error}, data={result.data}"
                )
            self.state.applied_positions.add(position_id)
            self.state.application_finished = True
            self.state.session_status = SessionStatus.APPLIED

    async def _finish_apply(self) -> None:
        """
        apply/finish を実行し、登録・応募完了状態を反映する。

        Returns:
            None
        """
        self._log_action("apply_finish_started")
        result = await self._api_post("apply/finish")
        if result.http_status != 200:
            self._log_action(
                "apply_finish_failed",
                http_status=result.http_status,
                error=result.error,
                data=result.data,
            )
            self.state.finish_reason = "apply_finish_failed"
            return
        if (
            isinstance(result.data, dict)
            and result.data.get("SessionStatus") is not None
        ):
            self.state.session_status = SessionStatus(result.data["SessionStatus"])

        if self.state.session_status in (
            SessionStatus.REGISTERED,
            SessionStatus.APPLIED,
        ):
            self.state.registration_finished = True
        if self.state.session_status == SessionStatus.APPLIED:
            self.state.application_finished = True
        self._log_action(
            "apply_finish_completed",
            session_status=int(self.state.session_status),
            registration_finished=self.state.registration_finished,
            application_finished=self.state.application_finished,
        )

    async def _apply_registered_positions(self) -> None:
        """
        登録済みセッションに対して未確定ポジション応募を確定する。

        Returns:
            None
        """
        if not self.state.applied_positions or self.state.application_finished:
            return

        for position_id in list(self.state.applied_positions):
            self._log_action(
                "registered_position_apply_submitted", position_id=position_id
            )
            result = await self._api_post(f"apply/position/{position_id}")
            if result.http_status != 200:
                self._log_action(
                    "registered_apply_submit_failed",
                    position_id=position_id,
                    http_status=result.http_status,
                    error=result.error,
                    data=result.data,
                )
                raise RuntimeError(
                    f"登録済み応募に失敗しました: http_status={result.http_status}, "
                    f"error={result.error}, data={result.data}"
                )
            self.state.application_finished = True
            self.state.session_status = SessionStatus.APPLIED
            return

    def _is_apply_finished(self) -> bool:
        """
        現在の apply_mode と session 状態から応募完了判定を返す。

        Returns:
            bool: 応募完了とみなせる場合 True
        """
        apply_mode = self.seed.run_hints.apply_mode
        if apply_mode == ApplyMode.NONE:
            return False
        if apply_mode == ApplyMode.REGISTRATION_ONLY:
            return self.state.registration_finished or self.state.session_status in (
                SessionStatus.REGISTERED,
                SessionStatus.APPLIED,
            )
        return (
            self.state.application_finished
            or self.state.session_status == SessionStatus.APPLIED
        )

    def _should_stop(self) -> bool:
        """
        終了ポリシー・会話回数・応募完了状態から停止判定を返す。

        Returns:
            bool: 実行を停止すべき場合 True
        """
        if self.state.finish_reason:
            return True

        rounds_exhausted = (
            self.max_rounds > 0 and self.state.round_count >= self.max_rounds
        )
        apply_finished = self._is_apply_finished()

        if self.finish_policy == FinishPolicy.MAX_ROUNDS:
            if rounds_exhausted:
                self.state.finish_reason = "max_rounds"
                return True
            return False

        if self.finish_policy == FinishPolicy.APPLY_FINISHED:
            if apply_finished:
                self.state.finish_reason = "apply_finished"
                return True
            return False

        if rounds_exhausted:
            self.state.finish_reason = "max_rounds"
            return True
        if apply_finished:
            self.state.finish_reason = "apply_finished"
            return True
        return False

    def _resolve_finish_reason(self) -> str:
        """
        最終的な finish_reason を解決して返す。

        Returns:
            str: 終了理由の文字列
        """
        if self.state.finish_reason:
            return self.state.finish_reason

        rounds_exhausted = (
            self.max_rounds > 0 and self.state.round_count >= self.max_rounds
        )
        apply_finished = self._is_apply_finished()

        if rounds_exhausted:
            return "max_rounds"
        if apply_finished:
            return "apply_finished"
        return "completed"

    async def _restore_main_history(self) -> None:
        """
        メインチャット履歴を取得して内部状態へ復元する。

        Returns:
            None
        """
        if self.state.main_history_restored:
            return
        result = await self._api_get("chat/previous")
        if result.http_status != 200 or not isinstance(result.data, dict):
            return
        restored_count = len(result.data.get("PreviousChatHistories", []))

        for raw_item in result.data.get("PreviousChatHistories", []):
            record = HistoryRecord.model_validate(raw_item)
            self._validate_history_record(record, "chat/previous")
            self._append_history_item(
                None,
                {
                    "role": record.Role,
                    "type": record.Type,
                    "message_id": record.MessageID,
                    "message": record.Message
                    if isinstance(record.Message, str)
                    else json.dumps(record.Message, ensure_ascii=False),
                },
            )
        self._sync_last_agent_message_from_history()
        self.state.main_history_restored = True
        self._log_action("main_history_restored", items=restored_count)

    async def _restore_position_history(self, position_id: str) -> None:
        """
        指定ポジションの詳細チャット履歴を復元する。

        Args:
            position_id (str): ポジションID

        Returns:
            None
        """
        if position_id in self.state.restored_position_histories:
            self._log_action(
                "position_history_restore_skipped",
                position_id=position_id,
                reason="already_restored",
            )
            return
        if self.state.position_histories.get(position_id):
            self.state.restored_position_histories.add(position_id)
            self._log_action(
                "position_history_restore_skipped",
                position_id=position_id,
                reason="already_loaded_locally",
            )
            return

        self._log_action("position_history_restore_started", position_id=position_id)
        exists = await self._api_get(f"chat/{position_id}/exist")
        if exists.http_status != 200:
            self._log_action(
                "position_history_restore_skipped",
                position_id=position_id,
                reason="exist_check_failed",
                http_status=exists.http_status,
                error=exists.error,
            )
            return

        result = await self._api_get(f"chat/previous/{position_id}")
        if result.http_status != 200 or not isinstance(result.data, dict):
            self._log_action(
                "position_history_restore_skipped",
                position_id=position_id,
                reason="history_fetch_failed",
                http_status=result.http_status,
                error=result.error,
            )
            return
        restored_count = len(result.data.get("PreviousChatHistories", []))

        for raw_item in result.data.get("PreviousChatHistories", []):
            record = HistoryRecord.model_validate(raw_item)
            self._validate_history_record(record, f"chat/previous/{position_id}")
            self._append_history_item(
                position_id,
                {
                    "role": record.Role,
                    "type": record.Type,
                    "message_id": record.MessageID,
                    "message": record.Message
                    if isinstance(record.Message, str)
                    else json.dumps(record.Message, ensure_ascii=False),
                },
            )
        self.state.restored_position_histories.add(position_id)
        self._log_action(
            "position_history_restored",
            position_id=position_id,
            items=restored_count,
        )

    async def _fetch_recommendation_positions(
        self, search_result: dict[str, Any]
    ) -> list[str]:
        """
        検索結果とレコメンドを集約し、候補ポジションID一覧を返す。

        Args:
            search_result (dict[str, Any]): ポジション検索結果

        Returns:
            list[str]: おすすめを含むポジションIDリスト
        """
        position_ids = self._normalize_position_ids(
            [position.get("ID") for position in search_result.get("Positions", [])]
        )
        search_key = search_result.get("SearchKey", "")

        for recommendation in search_result.get("Recommendations", []):
            theme = recommendation.get("Theme")
            if not theme:
                continue
            result = await self._api_get(
                f"positions/recommendations/{search_key}/{theme}",
                source_component=SOURCE_COMPONENT_RECOMMENDATION,
            )
            if result.http_status != 200 or not isinstance(result.data, dict):
                continue
            for position in result.data.get("Positions", []):
                position_id = str(position["ID"])
                self._merge_position_snapshot(position_id, position)
                position_ids.append(position_id)
        self._log_action(
            "recommendation_positions_loaded",
            search_key=search_key,
            position_count=len(position_ids),
        )
        return position_ids

    async def _fetch_position_detail_context(self, position_id: str) -> str:
        """
        求人・企業・事業情報を取得して詳細会話用コンテキストを生成する。

        Args:
            position_id (str): ポジションID

        Returns:
            str: 求人詳細チャット開始用メッセージ
        """
        self._log_action("position_detail_fetch_started", position_id=position_id)
        position_result, company_result, business_result = await asyncio.gather(
            self._api_get(
                f"positions/detail/{position_id}",
                source_component=SOURCE_COMPONENT_POSITION,
            ),
            self._api_get(f"companies/detail/{position_id}"),
            self._api_get(f"businesses/detail/{position_id}"),
        )

        if position_result.http_status != 200 or not isinstance(
            position_result.data, dict
        ):
            self._log_action(
                "position_detail_fetch_failed",
                position_id=position_id,
                http_status=position_result.http_status,
                error=position_result.error,
                data=position_result.data,
            )
            raise RuntimeError(
                f"求人情報を取得できませんでした: {position_id}, "
                f"http_status={position_result.http_status}, error={position_result.error}"
            )

        self._merge_position_snapshot(position_id, position_result.data)
        message = f"求人情報を取得しました。下記となります。この求人に対して、質問してください。\n\n求人情報: {position_result.data}"
        if company_result.http_status == 200 and company_result.data:
            message += f"\n\n企業情報: {company_result.data}"
        if business_result.http_status == 200 and business_result.data:
            message += f"\n\n事業情報: {business_result.data}"
        self._log_action(
            "position_detail_fetch_completed",
            position_id=position_id,
            company_status=company_result.http_status,
            business_status=business_result.http_status,
        )
        return message

    def _choose_position_id(
        self, position_ids: list[str], *, prefer_random: bool = False
    ) -> str | None:
        """
        候補ポジションIDから選択戦略に従って1件選ぶ。

        Args:
            position_ids (list[str]): 候補ポジションIDリスト
            prefer_random (bool): True の場合はランダム選択を優先

        Returns:
            str | None: 選択されたポジションID。候補がない場合は None。
        """
        unique_ids = list(dict.fromkeys(position_ids))
        if not unique_ids:
            return None
        if (
            prefer_random
            or self.seed.run_hints.position_selection
            == PositionSelectionStrategy.RANDOM
        ):
            return random.choice(unique_ids)
        return unique_ids[0]

    async def _leave_position_detail_chat(self, position_id: str) -> None:
        """
        ポジション詳細チャットを要約してメインチャットへ戻る。

        Args:
            position_id (str): ポジションID

        Returns:
            None
        """
        self._log_action("position_detail_exit_started", position_id=position_id)
        await self._send_ws_action(
            self._build_chat_payload(
                request_type=ChatRequestType.SUMMARIZE_POSITION,
                previous_page=PageName.POSITION_DETAIL,
                current_page=PageName.CHAT,
                position_id=position_id,
            )
        )
        self.state.current_page = PageName.CHAT
        self.state.active_position_id = None
        self.state.last_agent_message = POSITION_BACK_TO_CHAT_PROMPT
        self._log_action("position_detail_exited", position_id=position_id)

    async def _enter_position_detail_chat(self, position_id: str) -> None:
        """
        ポジション詳細チャットへ入り、初期コンテキストを準備する。

        Args:
            position_id (str): ポジションID

        Returns:
            None
        """
        self.state.active_position_id = position_id
        self.state.current_page = PageName.POSITION_DETAIL
        self._log_action("position_detail_entered", position_id=position_id)

        if self.restore_history_on_restart:
            await self._restore_position_history(position_id)

        if self.state.position_histories.get(position_id):
            self._log_action(
                "position_detail_context_source",
                position_id=position_id,
                source="restored_history",
            )
            self._sync_last_agent_message_from_history(position_id)
        else:
            self._log_action(
                "position_detail_context_source",
                position_id=position_id,
                source="detail_api",
            )
            self.state.last_agent_message = await self._fetch_position_detail_context(
                position_id
            )

    async def _run_position_detail_chat(self, position_id: str) -> None:
        """
        指定ポジションの詳細チャット往復を実行する。

        Args:
            position_id (str): ポジションID

        Returns:
            None
        """
        await self._enter_position_detail_chat(position_id)

        previous_page = PageName.CHAT
        turns = max(self.seed.run_hints.position_detail_turns, 0)
        for _ in range(turns):
            if self._should_stop():
                return
            if await self._maybe_randomly_restart_connection("position_detail"):
                continue
            if self.debug_mode:
                input("ENTER for continue, Ctrl+C to exit")

            exchange = await self._perform_chat_turn(
                current_page=PageName.POSITION_DETAIL,
                previous_page=previous_page,
                position_id=position_id,
            )
            previous_page = PageName.POSITION_DETAIL
            if exchange.response_type != ChatResponseType.MESSAGE:
                break

        if self.auto_run_profile_apply:
            await self._start_or_add_apply(position_id)

        await self._leave_position_detail_chat(position_id)

    async def _handle_position_search_result(
        self,
        search_result: dict[str, Any],
        *,
        prefer_random_selection: bool = False,
        source: str = "position_search_result",
    ) -> None:
        """
        ポジション検索結果を処理し、詳細チャットへ遷移する。

        Args:
            search_result (dict[str, Any]): ポジション検索結果
            prefer_random_selection (bool): True の場合は候補選択でランダム優先

        Returns:
            None
        """
        self.state.pending_position_search_result = None
        validated_search_result = self._validate_position_search_result_payload(
            search_result,
            source,
        )
        self._update_search_filter_state(validated_search_result, source=source)
        search_key = search_result.get("SearchKey", "")
        if search_key:
            existing_result = self.state.search_results.get(search_key, {})
            merged_result = {**existing_result, **validated_search_result}
            existing_positions = existing_result.get("Positions", [])
            merged_positions = list(existing_positions)
            seen_ids = {str(position.get("ID")) for position in existing_positions}
            for position in validated_search_result.get("Positions", []):
                position_id = str(position["ID"])
                if position_id not in seen_ids:
                    merged_positions.append(position)
                    seen_ids.add(position_id)
                self._merge_position_snapshot(position_id, position)
            merged_result["Positions"] = merged_positions
            self.state.search_results[search_key] = merged_result
            search_result = merged_result
        else:
            search_result = validated_search_result
            for position in search_result.get("Positions", []):
                self._merge_position_snapshot(str(position["ID"]), position)

        self._log_action(
            "position_search_result_received",
            search_key=search_key,
            positions=len(search_result.get("Positions", [])),
            tool_name=self.state.active_tool_name,
        )
        position_ids = await self._fetch_recommendation_positions(search_result)
        position_id = self._choose_position_id(
            position_ids,
            prefer_random=prefer_random_selection,
        )
        if not position_id:
            self._log_info("ポジション検索結果が空でした。")
            return
        self._log_action("position_selected", position_id=position_id)
        await self._run_position_detail_chat(position_id)

    async def _handle_position_search_link(self, search_link: dict[str, Any]) -> None:
        """
        position_search_link を辿って再検索結果を取得する。

        Args:
            search_link (dict[str, Any]): position_search_link の内容

        Returns:
            None
        """
        self.state.pending_position_search_link = None
        search_link = self._validate_position_search_link_payload(
            search_link,
            "position_search_link",
        )
        if not self.auto_follow_position_search_link:
            return

        tool_call_id = search_link.get("ToolCallId")
        if not tool_call_id:
            raise RuntimeError("position_search_link に ToolCallId がありません")
        self.state.search_links[tool_call_id] = search_link
        self._log_action("position_research_started", tool_call_id=tool_call_id)

        result = await self._api_get(f"positions/re-search/{tool_call_id}")
        if result.http_status != 200 or not isinstance(result.data, dict):
            self._log_action(
                "position_research_failed",
                tool_call_id=tool_call_id,
                http_status=result.http_status,
                error=result.error,
                data=result.data,
            )
            raise RuntimeError(
                f"positions/re-search に失敗しました: {tool_call_id}, "
                f"http_status={result.http_status}, error={result.error}, data={result.data}"
            )

        self.state.pending_position_search_result = result.data
        self._log_action("position_research_completed", tool_call_id=tool_call_id)

    async def _handle_jobtype_search_result(
        self, jobtype_search: dict[str, Any]
    ) -> None:
        """
        受信した職種候補から選択を生成してサーバーへ送信する。

        Args:
            jobtype_search (dict[str, Any]): 職種検索結果ペイロード

        Returns:
            None
        """
        self.state.pending_jobtype_search = None
        jobtype_search = self._validate_jobtype_search_result_payload(
            jobtype_search,
            "jobtype_search_result",
        )
        jobtypes = jobtype_search.get("Jobtypes", [])
        if not jobtypes:
            return
        self._log_action(
            "jobtype_options_received",
            options=[item["Name"] for item in jobtypes],
        )
        selected_names = self._choose_jobtype_names(jobtypes)
        self._log_action(
            "jobtype_selection_generated",
            selected_jobtypes=selected_names,
            option_count=len(jobtypes),
        )
        await self._send_jobtype_selection(selected_names or None)
        if await self._run_jobtype_specific_search():
            return

    async def _handle_workflow(self, workflow: dict[str, Any]) -> None:
        """
        受信した workflow payload から回答を作成しサーバーへ送信する。

        Args:
            workflow (dict[str, Any]): workflow ペイロード

        Returns:
            None
        """
        source = "workflow_payload"
        self._require_contract(
            isinstance(workflow, dict) and "id" in workflow,
            category="contract_error",
            source=source,
            details="workflow payload must be object with id",
            actual=workflow,
        )
        workflow_id = workflow["id"]
        self._log_action("workflow_received", workflow_id=workflow_id)

        steps = workflow.get("steps", [])
        self._require_contract(
            isinstance(steps, list),
            category="contract_error",
            source=source,
            details="workflow.steps must be list",
            actual=steps,
        )

        if workflow_id == "job_match_diagnosis":
            answers = await self._build_job_match_diagnosis_answers(steps, source)
        else:
            answers = self._build_default_workflow_answers(steps, source)

        self._log_action(
            "workflow_submitting",
            workflow_id=workflow_id,
            step_count=len(answers),
        )
        payload = self._build_chat_payload(
            request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            previous_page=PageName.CHAT,
            current_page=PageName.CHAT,
            message=json.dumps(
                {"workflow_id": workflow_id, "answers": answers},
                ensure_ascii=False,
            ),
        )
        await self._send_ws_action(payload)
        self._log_action("workflow_handled", workflow_id=workflow_id)

    def _build_default_workflow_answers(
        self,
        steps: list[Any],
        source: str,
    ) -> dict[str, list[Any]]:
        """汎用 workflow のデフォルト回答を構築する。"""
        answers: dict[str, list[Any]] = {}
        for step in steps:
            self._require_contract(
                isinstance(step, dict) and "id" in step,
                category="contract_error",
                source=source,
                details="workflow step must be object with id",
                actual=step,
            )
            options = step.get("options", [])
            if not options:
                continue
            option = options[0]
            self._require_contract(
                isinstance(option, dict),
                category="contract_error",
                source=source,
                details="workflow step option must be object",
                actual=option,
            )
            if option.get("items"):
                items = option["items"]
                self._require_contract(
                    isinstance(items, list)
                    and len(items) > 0
                    and isinstance(items[0], dict)
                    and "value" in items[0],
                    category="contract_error",
                    source=source,
                    details="workflow option items[0] must be object with value",
                    actual=items,
                )
                first_value = items[0]
            else:
                self._require_contract(
                    "value" in option,
                    category="contract_error",
                    source=source,
                    details="workflow option must have value",
                    actual=option,
                )
                first_value = option
            answers[str(step["id"])] = [first_value]
        return answers

    def _extract_workflow_items(self, step: dict[str, Any], source: str) -> list[dict[str, Any]]:
        """step.options から value を持つ候補 item を抽出する。"""
        options = step.get("options", [])
        self._require_contract(
            isinstance(options, list),
            category="contract_error",
            source=source,
            details="workflow step options must be list",
            actual=step,
        )

        candidates: list[dict[str, Any]] = []
        for option in options:
            self._require_contract(
                isinstance(option, dict),
                category="contract_error",
                source=source,
                details="workflow step option must be object",
                actual=option,
            )
            items = option.get("items")
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and "value" in item:
                        candidates.append(item)
                continue
            if "value" in option:
                candidates.append(option)

        return candidates

    async def _build_job_match_diagnosis_answers(
        self,
        steps: list[Any],
        source: str,
    ) -> dict[str, list[Any]]:
        """job_match_diagnosis 用に browser と同じ順序で回答を構築する。"""
        step_map: dict[str, dict[str, Any]] = {}
        for step in steps:
            self._require_contract(
                isinstance(step, dict) and "id" in step,
                category="contract_error",
                source=source,
                details="workflow step must be object with id",
                actual=step,
            )
            step_map[str(step["id"])] = step

        self._require_contract(
            "1" in step_map,
            category="contract_error",
            source=source,
            details="job_match_diagnosis requires step 1",
            actual=steps,
        )

        step1_candidates = self._extract_workflow_items(step_map["1"], source)
        self._require_contract(
            len(step1_candidates) >= 3,
            category="contract_error",
            source=source,
            details="job_match_diagnosis step 1 must include at least 3 candidate options",
            actual=step1_candidates,
        )

        step1_answers = step1_candidates[:3]
        step2_answers: list[dict[str, Any]] = []

        search_payload = {
            "answers": {
                "1": step1_answers,
                "2": step2_answers,
            }
        }
        self._log_action(
            "workflow_jobtype_search_submitting",
            workflow_id="job_match_diagnosis",
            step1_count=len(step1_answers),
        )
        result = await self._api_post(
            "workflow/job_match_diagnosis/search_occupations",
            data=search_payload,
        )
        self._require_contract(
            result.http_status == 200 and isinstance(result.data, list),
            category="rest_format_invalid",
            source="workflow/job_match_diagnosis/search_occupations",
            details="search_occupations response must be list with status 200",
            actual={"status": result.http_status, "data": result.data},
        )

        step3_answers: list[dict[str, Any]] = []
        for item in result.data:
            if not isinstance(item, dict):
                continue
            jobtype_label = item.get("職種名")
            jobtype_id = item.get("ID")
            if isinstance(jobtype_label, str) and jobtype_label and jobtype_id not in (
                None,
                "",
            ):
                step3_answers.append({"label": jobtype_label, "value": jobtype_id})

        self._require_contract(
            len(step3_answers) > 0,
            category="rest_format_invalid",
            source="workflow/job_match_diagnosis/search_occupations",
            details="search_occupations must return at least one selectable jobtype",
            actual=result.data,
        )

        self._log_action(
            "workflow_jobtype_search_completed",
            workflow_id="job_match_diagnosis",
            candidate_count=len(step3_answers),
        )

        return {
            "1": step1_answers,
            "2": step2_answers,
            "3": [step3_answers[0]],
        }

    async def _handle_pending_actions(self) -> bool:
        """
        保留中のジョブタイプ/検索リンク/検索結果アクションを順次処理する。

        Returns:
            bool: 保留アクションを処理した場合 True
        """
        if self.state.pending_workflow:
            pending = self.state.pending_workflow
            self.state.pending_workflow = None
            await self._handle_workflow(pending)
            return True
        if self.state.pending_jobtype_search:
            await self._handle_jobtype_search_result(self.state.pending_jobtype_search)
            return True
        if self.state.pending_position_search_link:
            await self._handle_position_search_link(
                self.state.pending_position_search_link
            )
            return True
        if self.state.pending_position_search_result:
            await self._handle_position_search_result(
                self.state.pending_position_search_result
            )
            return True
        return False

    async def _handle_profile_and_apply_actions(self) -> bool:
        """
        必要に応じてプロフィール保存・応募完了処理を実行する。

        Returns:
            bool: プロフィール・応募処理を実行した場合 True
        """
        if not self.auto_run_profile_apply:
            return False

        if self.state.session_status in (
            SessionStatus.REGISTERING,
            SessionStatus.APPLYING,
        ):
            await self._ensure_profile_sections_saved()
            await self._finish_apply()
            if self.state.session_status == SessionStatus.REGISTERED:
                await self._apply_registered_positions()
            return True

        if self.state.session_status == SessionStatus.REGISTERED:
            await self._apply_registered_positions()
            return self.state.application_finished

        return False

    def _update_state_from_exchange(self, exchange: ResponseExchange) -> None:
        """
        サーバー応答を履歴・セッション状態・保留アクションへ反映する。

        Args:
            exchange (ResponseExchange): サーバー応答

        Returns:
            None
        """
        self._set_session(exchange.session_id, exchange.session_status)

        assistant_message_parts: list[str] = []

        for event in exchange.events:
            self._validate_ws_event_contract(event)
            if event.response_type == ChatResponseType.END:
                continue
            if self._is_ignored_server_message(event):
                self._log_info("エージェントサーバー応答を無視: token_usage")
                continue

            item = {
                "role": event.role,
                "type": event.response_type,
                "message_id": event.message_id,
                "message": event.message,
            }
            self._append_history_item(event.position_id, item)

            if (
                event.response_type == ChatResponseType.MESSAGE
                and event.role == LLMMessageRole.ASSISTANT
            ):
                assistant_message_parts.append(event.message)
            elif event.response_type == ChatResponseType.POSITION_SEARCH_RESULT:
                parsed = self._parse_json_message(event.message)
                self._validate_position_search_result_payload(
                    parsed,
                    "websocket:position_search_result",
                )
                self._update_search_filter_state(
                    parsed,
                    source="websocket:position_search_result",
                )
                search_key = parsed.get("SearchKey")
                if search_key:
                    self.state.search_results[search_key] = {
                        **self.state.search_results.get(search_key, {}),
                        **parsed,
                    }
                self.state.pending_position_search_result = parsed
                self._log_info("エージェントサーバー応答: position_search_result")
            elif event.response_type == ChatResponseType.POSITION_SEARCH_LINK:
                parsed = self._validate_position_search_link_payload(
                    self._parse_json_message(event.message),
                    "websocket:position_search_link",
                )
                tool_call_id = parsed.get("ToolCallId")
                if tool_call_id:
                    self.state.search_links[tool_call_id] = parsed
                self.state.pending_position_search_link = parsed
                self._log_info("エージェントサーバー応答: position_search_link")
            elif event.response_type == ChatResponseType.JOBTYPE_SEARCH_RESULT:
                self.state.pending_jobtype_search = (
                    self._validate_jobtype_search_result_payload(
                        self._parse_json_message(event.message),
                        "websocket:jobtype_search_result",
                    )
                )
                self._log_info("エージェントサーバー応答: jobtype_search_result")
            elif event.response_type == ChatResponseType.WORKFLOW:
                self.state.pending_workflow = self._parse_json_message(event.message)
                self._log_info("エージェントサーバー応答: workflow")
            elif event.response_type == ChatResponseType.ERROR:
                if event.message == self.SYSTEM_ERROR_MESSAGE:
                    self.state.finish_reason = "system_error"
                self._log_info(
                    f"サーバーエラー [{self._session_log_context()}]: {event.message}",
                    console=True,
                )

        if assistant_message_parts:
            self.state.last_agent_message = "".join(assistant_message_parts)
            self._log_info(
                f"エージェントサーバーメッセージ:\n{self.state.last_agent_message}"
            )

        if exchange.is_maintenance:
            self.state.finish_reason = "maintenance"

    async def _perform_chat_turn(
        self,
        *,
        current_page: PageName,
        previous_page: PageName,
        position_id: str | None = None,
    ) -> ResponseExchange:
        """
        求職者LLMの発話生成からサーバー応答受信までの1ターンを実行する。

        Args:
            current_page (PageName): 現在ページ
            previous_page (PageName): 遷移前ページ
            position_id (str | None): 対象ポジションID

        Returns:
            ResponseExchange: サーバー応答
        """
        agent_invoke_time, response_message = await self.client.ask_job_seeker(
            self.state.last_agent_message,
            self._recent_dialogue_context(position_id),
        )
        self._log_info(f"求職LLMメッセージ:\n{response_message}")

        message_id = self._next_message_id("input")
        self._append_history_item(
            position_id,
            {
                "role": LLMMessageRole.USER,
                "type": ChatResponseType.MESSAGE,
                "message_id": message_id,
                "message": response_message,
            },
        )

        payload = self._build_chat_payload(
            request_type=ChatRequestType.CHAT,
            previous_page=previous_page,
            current_page=current_page,
            message=response_message,
            position_id=position_id,
            current_message_id=message_id,
            is_voice=False,
        )
        await self.client.send_request(payload)

        exchange = await self.client.receive_exchange()
        self.state.round_count += 1
        self._record_exchange_stats(exchange, agent_invoke_time)
        self._update_state_from_exchange(exchange)
        return exchange

    async def run(self) -> dict[str, Any]:
        """
        E2Eシナリオを実行し、結果サマリを返す。

        Returns:
            dict[str, Any]: 実行結果データ
        """
        try:
            await self.api_client.open()
            await self._establish_connection()

            while True:
                if self._should_stop():
                    break

                if await self._maybe_randomly_restart_connection("main_chat"):
                    continue

                if await self._handle_pending_actions():
                    continue

                if await self._run_jobtype_specific_search():
                    continue

                if await self._handle_profile_and_apply_actions():
                    continue

                if self.debug_mode:
                    input("ENTER for continue, Ctrl+C to exit")

                await self._perform_chat_turn(
                    current_page=PageName.CHAT,
                    previous_page=PageName.CHAT,
                )

        except KeyboardInterrupt:
            self.state.finish_reason = "keyboard_interrupt"
            self._log_info("接続切断中...")
        except Exception as e:
            self.state.finish_reason = self.state.finish_reason or "error"
            self._log_info(
                f"予期しないエラー [{self._session_log_context()}]: {e}",
                console=True,
            )
            self.logger.exception("予期しないエラー詳細")
        finally:
            await self.client.close()
            await self.api_client.close()
            self._log_info("接続切断済")

        self.state.finish_reason = self._resolve_finish_reason()

        return {
            "persona": self.client_id,
            "model": self.model_name,
            "turns": self.state.round_count,
            "reconnects": self.state.reconnect_count,
            "finish_reason": self.state.finish_reason,
            "session_id": self.state.session_id,
            "session_status": int(self.state.session_status),
            "stats": self.conversation_stats,
        }
