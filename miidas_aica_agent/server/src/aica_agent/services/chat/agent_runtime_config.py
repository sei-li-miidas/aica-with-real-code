import inspect
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

DEFAULT_SERVICE_VARIANT = "legacy"
REFACTORED_SERVICE_VARIANT = "refactored"
DEFAULT_AGENT_MODEL = "openai/gpt-4.1"
DEFAULT_API_STYLE = "responses"
COMPLETIONS_API_STYLE = "completions"
UNKNOWN_SUMMARY_MODEL = "not-configured"
AGENT_RUNTIME_KEY = "agent_runtime"
SUPPORTED_SERVICE_VARIANTS = frozenset(
    {DEFAULT_SERVICE_VARIANT, REFACTORED_SERVICE_VARIANT}
)
SUPPORTED_API_STYLES = frozenset({DEFAULT_API_STYLE, COMPLETIONS_API_STYLE})

_MISSING = object()


def _can_call_without_arguments(value: Any) -> bool:
    """callable を引数なしで実行できるかを署名から判定する。"""
    signature = inspect.signature(value)
    for parameter in signature.parameters.values():
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if parameter.default is inspect.Parameter.empty:
            return False
    return True


@dataclass(frozen=True)
class AgentRuntimeConfig:
    """chat runtime 設定を保持するデータクラス。"""

    service_variant: str = DEFAULT_SERVICE_VARIANT
    agent_model: str = DEFAULT_AGENT_MODEL
    api_style: str = DEFAULT_API_STYLE


def _resolve(value: Any) -> Any:
    """設定値を1段だけ展開する。

    プロバイダー:
        `value()` で実体を返すオブジェクト。
        例: dependency_injector の provider や Configuration の節。
    属性オブジェクト:
        `.agent_runtime` のように属性として値を持つオブジェクト。
        例: SimpleNamespace や設定用のオブジェクト。
    単純値:
        それ以上展開しない値。
        例: 文字列、数値、真偽値。
    """
    if value is _MISSING:
        return _MISSING
    if callable(value):
        if not _can_call_without_arguments(value):
            return _MISSING
        return value()
    return value


def _read(config: Any, *path: str, default: Any = _MISSING) -> Any:
    """ネストした config から値を順に辿って取り出す。"""
    current = config
    for key in path:
        current = _resolve(current)
        if current is _MISSING:
            return default
        if isinstance(current, Mapping):
            current = current.get(key, _MISSING)
        else:
            current = getattr(current, key, _MISSING)
    current = _resolve(current)
    if current is _MISSING:
        return default
    return current


def get_service_variant(config: Any | None = None) -> str:
    """agent runtime の service_variant を返す。"""
    value = _read(
        config,
        AGENT_RUNTIME_KEY,
        "service_variant",
        default=DEFAULT_SERVICE_VARIANT,
    )
    if value is None:
        return DEFAULT_SERVICE_VARIANT
    return str(value).strip() or DEFAULT_SERVICE_VARIANT


def get_agent_model(config: Any | None = None) -> str:
    """agent runtime の agent_model を返す。"""
    value = _read(
        config,
        AGENT_RUNTIME_KEY,
        "agent_model",
        default=DEFAULT_AGENT_MODEL,
    )
    if value is None:
        return DEFAULT_AGENT_MODEL
    return str(value).strip() or DEFAULT_AGENT_MODEL


def get_api_style(config: Any | None = None) -> str:
    """agent runtime の api_style を返す。"""
    value = _read(
        config,
        AGENT_RUNTIME_KEY,
        "api_style",
        default=DEFAULT_API_STYLE,
    )
    if value is None:
        return DEFAULT_API_STYLE
    return str(value).strip() or DEFAULT_API_STYLE


def get_model_list(config: Any | None = None) -> list[Any]:
    """設定された model_list を返す。"""
    value = _read(config, "model_list", default=[])
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError("model_list must be a list")
    return value


def _read_model_entry(entry: Any, key: str, default: Any = _MISSING) -> Any:
    entry = _resolve(entry)
    if entry is _MISSING:
        return default
    if isinstance(entry, Mapping):
        value = entry.get(key, default)
    else:
        value = getattr(entry, key, default)
    value = _resolve(value)
    return default if value is _MISSING else value


def get_summary_model(config: Any | None = None) -> str:
    """会話要約に使う summary model 名を返す。"""
    for model_config in get_model_list(config):
        use_for = _read_model_entry(model_config, "use_for", default=[])
        if isinstance(use_for, str):
            targets = {use_for}
        else:
            targets = set(use_for or [])
        if "summary" not in targets:
            continue

        model_name = _read_model_entry(model_config, "model", default="")
        return str(model_name).strip() or UNKNOWN_SUMMARY_MODEL
    return UNKNOWN_SUMMARY_MODEL


def resolve_default_agent_model(config: Any | None = None) -> str:
    """エンドポイントで使う default の agent model を返す。"""
    return get_agent_model(config)


def resolve_default_api_style(config: Any | None = None) -> str:
    """エンドポイントで使う default の api style を返す。"""
    return get_api_style(config)


def resolve_agent_runtime_config(config: Any | None = None) -> AgentRuntimeConfig:
    """設定から `AgentRuntimeConfig` を組み立てる。"""
    return AgentRuntimeConfig(
        service_variant=get_service_variant(config),
        agent_model=get_agent_model(config),
        api_style=get_api_style(config),
    )


def log_startup_runtime_config(logger: Any, config: Any | None = None) -> None:
    """Phase 6 release evidence 用の startup runtime 設定ログを出す。"""
    logger.info(
        "startup runtime config: service_variant=%s agent_model=%s summary_model=%s backend=%s",
        get_service_variant(config),
        get_agent_model(config),
        get_summary_model(config),
        get_api_style(config),
    )


def log_chat_turn_runtime(
    logger: Any,
    config: Any | None,
    chat_svc: Any,
    *,
    request_type: Any | None = None,
) -> None:
    """Phase 6 release evidence 用の chat turn runtime ログを出す。"""
    service_class = f"{chat_svc.__class__.__module__}.{chat_svc.__class__.__name__}"
    logger.info(
        "chat turn runtime: service_variant=%s agent_model=%s backend=%s chat_service=%s request_type=%s",
        get_service_variant(config),
        get_agent_model(config),
        get_api_style(config),
        service_class,
        getattr(request_type, "value", request_type),
    )
