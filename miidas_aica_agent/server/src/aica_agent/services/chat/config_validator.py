from collections.abc import Mapping
from typing import Any

from services.chat.agent_runtime_config import (
    DEFAULT_API_STYLE,
    DEFAULT_SERVICE_VARIANT,
    REFACTORED_SERVICE_VARIANT,
    SUPPORTED_API_STYLES,
    SUPPORTED_SERVICE_VARIANTS,
    get_model_list,
    resolve_agent_runtime_config,
)


VALID_AGENT_RUNTIME_MATRIX = {
    DEFAULT_SERVICE_VARIANT: frozenset({DEFAULT_API_STYLE}),
    REFACTORED_SERVICE_VARIANT: SUPPORTED_API_STYLES,
}


class InvalidAgentRuntimeConfigError(ValueError):
    """agent runtime 設定が不正なときに送出する。"""


def _normalize_use_for(value: Any) -> list[str]:
    """`use_for` の値を比較しやすい文字列リストへ正規化する。"""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _collect_model_entries(model_list: list[Any]) -> list[dict[str, Any]]:
    """`model_list` を辞書の配列に集約する。"""
    entries: list[dict[str, Any]] = []
    for item in model_list:
        if isinstance(item, Mapping):
            entries.append(dict(item))
        else:
            entries.append(
                {
                    "model": getattr(item, "model", None),
                    "use_for": getattr(item, "use_for", None),
                }
            )
    return entries


def validate_agent_runtime_config(config: Any | None = None) -> None:
    """validity matrix で許可される agent runtime 設定か検証する。"""
    runtime = resolve_agent_runtime_config(config)

    if runtime.service_variant not in SUPPORTED_SERVICE_VARIANTS:
        allowed = ", ".join(sorted(SUPPORTED_SERVICE_VARIANTS))
        raise InvalidAgentRuntimeConfigError(
            f"service_variant: {runtime.service_variant} is not supported. Only {allowed} are valid."
        )

    if not runtime.agent_model:
        raise InvalidAgentRuntimeConfigError(
            "agent_runtime.agent_model must be configured"
        )

    if runtime.api_style not in SUPPORTED_API_STYLES:
        allowed = ", ".join(sorted(SUPPORTED_API_STYLES))
        raise InvalidAgentRuntimeConfigError(
            f"agent_runtime.api_style: {runtime.api_style} is not supported. Only {allowed} are valid."
        )

    allowed_api_styles = VALID_AGENT_RUNTIME_MATRIX.get(runtime.service_variant)
    if allowed_api_styles is None:
        raise InvalidAgentRuntimeConfigError(
            "VALID_AGENT_RUNTIME_MATRIX is missing an entry for service_variant=%s"
            % runtime.service_variant
        )

    if runtime.api_style not in allowed_api_styles:
        allowed = ", ".join(sorted(allowed_api_styles))
        raise InvalidAgentRuntimeConfigError(
            "agent_runtime.api_style=%s is not supported for service_variant=%s. Only %s are valid."
            % (runtime.api_style, runtime.service_variant, allowed)
        )

    try:
        model_list = get_model_list(config)
    except TypeError as exc:
        raise InvalidAgentRuntimeConfigError(str(exc)) from exc

    entries = _collect_model_entries(model_list)
    configured_agent_models = [
        entry.get("model")
        for entry in entries
        if "agent" in _normalize_use_for(entry.get("use_for"))
    ]

    if runtime.agent_model not in configured_agent_models:
        raise InvalidAgentRuntimeConfigError(
            "agent_runtime.agent_model=%s is not present in model_list use_for: agent"
            % runtime.agent_model
        )
