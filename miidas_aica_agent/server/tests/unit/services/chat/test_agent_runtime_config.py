from types import SimpleNamespace
from unittest.mock import Mock

import pytest

pytestmark = pytest.mark.pre_extraction_parity

from services.chat.agent_runtime_config import (
    AgentRuntimeConfig,
    COMPLETIONS_API_STYLE,
    DEFAULT_API_STYLE,
    DEFAULT_AGENT_MODEL,
    DEFAULT_SERVICE_VARIANT,
    get_api_style,
    get_agent_model,
    get_model_list,
    get_service_variant,
    get_summary_model,
    log_chat_turn_runtime,
    log_startup_runtime_config,
    resolve_agent_runtime_config,
    resolve_default_agent_model,
)


def test_resolve_defaults_when_agent_runtime_section_is_missing():
    """agent_runtime がなければ既定値にフォールバックすることを確認する。"""
    assert resolve_default_agent_model({}) == DEFAULT_AGENT_MODEL
    assert get_api_style({}) == DEFAULT_API_STYLE
    assert get_service_variant({}) == DEFAULT_SERVICE_VARIANT


def test_resolve_agent_runtime_config_from_mapping():
    """mapping 形式の config から runtime 設定を正しく組み立てる。"""
    config = {
        "agent_runtime": {
            "service_variant": "legacy",
            "agent_model": "openai/gpt-4.1",
            "api_style": DEFAULT_API_STYLE,
        }
    }

    runtime = resolve_agent_runtime_config(config)

    assert runtime == AgentRuntimeConfig(
        service_variant="legacy",
        agent_model="openai/gpt-4.1",
        api_style=DEFAULT_API_STYLE,
    )
    assert get_agent_model(config) == "openai/gpt-4.1"
    assert get_api_style(config) == DEFAULT_API_STYLE


def test_resolve_service_variant_from_mapping():
    """mapping 形式の config から refactored service_variant を正しく取り出す。"""
    config = {
        "agent_runtime": {
            "service_variant": "refactored",
            "agent_model": "openai/gpt-4.1",
            "api_style": COMPLETIONS_API_STYLE,
        }
    }

    assert get_service_variant(config) == "refactored"
    assert resolve_agent_runtime_config(config).service_variant == "refactored"
    assert get_api_style(config) == COMPLETIONS_API_STYLE


def test_get_model_list_from_mapping():
    """model_list を公開 API 経由で取得できることを確認する。"""
    model_list = [{"model": "openai/gpt-4.1", "use_for": ["agent"]}]
    assert get_model_list({"model_list": model_list}) == model_list


def test_get_summary_model_from_mapping():
    """model_list から summary model を取得できることを確認する。"""
    config = {
        "model_list": [
            {"model": "openai/gpt-4.1", "use_for": ["agent"]},
            {"model": "gpt-4.1-2025-04-14", "use_for": ["summary"]},
        ]
    }

    assert get_summary_model(config) == "gpt-4.1-2025-04-14"


def test_get_summary_model_returns_not_configured_when_missing():
    """summary 用 model がなければ log 用の明示値を返す。"""
    assert get_summary_model({"model_list": []}) == "not-configured"


def test_log_startup_runtime_config_includes_phase_6_fields():
    """startup log に Phase 6 で要求された runtime fields が含まれる。"""
    logger = Mock()
    config = {
        "agent_runtime": {
            "service_variant": "refactored",
            "agent_model": "openai/gpt-4.1",
        },
        "model_list": [{"model": "summary-model", "use_for": ["summary"]}],
    }

    log_startup_runtime_config(logger, config)

    logger.info.assert_called_once_with(
        "startup runtime config: service_variant=%s agent_model=%s summary_model=%s backend=%s",
        "refactored",
        "openai/gpt-4.1",
        "summary-model",
        "responses",
    )


def test_log_chat_turn_runtime_includes_variant_backend_and_service():
    """chat turn log に variant/backend/service が含まれる。"""
    logger = Mock()
    chat_svc = SimpleNamespace()

    log_chat_turn_runtime(
        logger,
        {
            "agent_runtime": {
                "service_variant": "legacy",
                "agent_model": "agent-model",
            }
        },
        chat_svc,
        request_type="chat",
    )

    logger.info.assert_called_once_with(
        "chat turn runtime: service_variant=%s agent_model=%s backend=%s chat_service=%s request_type=%s",
        "legacy",
        "agent-model",
        "responses",
        "types.SimpleNamespace",
        "chat",
    )


@pytest.mark.parametrize("config", [{}, None])
def test_get_model_list_returns_empty_list_when_not_configured(config):
    """model_list が未設定なら空リストを返すことを確認する。"""
    assert get_model_list(config) == []


@pytest.mark.parametrize(
    "model_list",
    [
        "openai/gpt-4.1",
        {"model": "openai/gpt-4.1", "use_for": ["agent"]},
    ],
)
def test_get_model_list_rejects_non_list_value(model_list):
    """model_list が list でなければ公開 API で拒否することを確認する。"""
    with pytest.raises(TypeError, match="model_list must be a list"):
        get_model_list({"model_list": model_list})


def test_resolve_agent_runtime_config_from_attribute_object():
    """属性アクセス型の config から runtime 設定を正しく組み立てる。"""
    config = SimpleNamespace(
        agent_runtime=SimpleNamespace(
            service_variant="legacy",
            agent_model="custom/agent-model",
            api_style=DEFAULT_API_STYLE,
        )
    )

    runtime = resolve_agent_runtime_config(config)

    assert runtime.service_variant == "legacy"
    assert runtime.agent_model == "custom/agent-model"
    assert runtime.api_style == DEFAULT_API_STYLE


def test_get_api_style_returns_default_when_value_is_missing_or_blank():
    """api_style が未設定なら既定値にフォールバックすることを確認する。"""
    assert get_api_style({}) == DEFAULT_API_STYLE
    assert get_api_style({"agent_runtime": {"api_style": None}}) == DEFAULT_API_STYLE
    assert get_api_style({"agent_runtime": {"api_style": ""}}) == DEFAULT_API_STYLE


def test_resolve_defaults_when_callable_needs_arguments():
    """引数必須の callable が来た場合でも既定値へ戻ることを確認する。"""

    class NeedsArgumentCallable:
        def __call__(self, required_argument):  # pragma: no cover - invoked indirectly
            return required_argument

    config = SimpleNamespace(
        agent_runtime=SimpleNamespace(
            service_variant=NeedsArgumentCallable(),
            agent_model=NeedsArgumentCallable(),
        )
    )

    assert get_service_variant(config) == DEFAULT_SERVICE_VARIANT
    assert get_agent_model(config) == DEFAULT_AGENT_MODEL


def test_resolve_executes_callable_with_only_optional_arguments():
    """任意引数だけの callable は引数なしで実行されることを確認する。"""

    class OptionalArgumentCallable:
        def __call__(self, value="legacy"):
            return value

    config = SimpleNamespace(
        agent_runtime=SimpleNamespace(
            service_variant=OptionalArgumentCallable(),
        )
    )

    assert get_service_variant(config) == "legacy"


def test_resolve_raises_type_error_from_zero_arg_callable():
    """引数不要 callable の内部 TypeError は握りつぶさないことを確認する。"""

    class BrokenCallable:
        was_called = False

        def __call__(self):
            self.was_called = True
            raise TypeError("internal configuration provider error")

    service_variant = BrokenCallable()
    config = SimpleNamespace(
        agent_runtime=SimpleNamespace(
            service_variant=service_variant,
        )
    )

    with pytest.raises(TypeError, match="internal configuration provider error"):
        get_service_variant(config)
    assert service_variant.was_called


def test_can_call_without_arguments_skips_var_positional_and_var_keyword():
    """VAR_POSITIONAL / VAR_KEYWORD パラメータは引数なし呼び出し判定でスキップされる。"""

    def func_with_var_args(*args, **kwargs):
        return "ok"

    # Both *args and **kwargs are VAR_POSITIONAL/VAR_KEYWORD; callable without arguments.
    assert (
        get_service_variant({"agent_runtime": {"service_variant": func_with_var_args}})
        == "ok"
    )


def test_get_service_variant_and_agent_model_return_default_when_value_is_none():
    """None が返ってきた場合にデフォルト値へフォールバックすることを確認する。"""
    config = {"agent_runtime": {"service_variant": None, "agent_model": None}}
    assert get_service_variant(config) == DEFAULT_SERVICE_VARIANT
    assert get_agent_model(config) == DEFAULT_AGENT_MODEL


def test_get_model_list_returns_empty_list_when_value_is_none():
    """model_list キーが存在しても値が None なら空リストを返すことを確認する。"""
    # Simulate a config provider that returns None for model_list
    assert get_model_list({"model_list": None}) == []


def test_get_summary_model_supports_string_use_for():
    """use_for が文字列でも summary target として扱えることを確認する。"""
    config = {
        "model_list": [
            {"model": "agent-model", "use_for": "agent"},
            {"model": "summary-model", "use_for": "summary"},
        ]
    }

    assert get_summary_model(config) == "summary-model"


def test_get_summary_model_reads_attribute_style_model_entry():
    """model_list の各要素が属性アクセス型でも summary model を解決できることを確認する。"""
    config = {
        "model_list": [
            SimpleNamespace(model="summary-attr", use_for=["summary"]),
        ]
    }

    assert get_summary_model(config) == "summary-attr"


def test_get_summary_model_skips_unresolvable_callable_entry():
    """引数必須 callable エントリは未解決扱いとなり、summary 解決を妨げないことを確認する。"""

    class NeedsArgEntry:
        def __call__(self, required):  # pragma: no cover - invoked indirectly
            return required

    config = {
        "model_list": [
            NeedsArgEntry(),
            {"model": "summary-ok", "use_for": ["summary"]},
        ]
    }

    assert get_summary_model(config) == "summary-ok"
