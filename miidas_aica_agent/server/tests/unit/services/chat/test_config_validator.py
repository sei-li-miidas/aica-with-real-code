import pytest
from unittest.mock import patch

pytestmark = pytest.mark.pre_extraction_parity

from services.chat.config_validator import (
    InvalidAgentRuntimeConfigError,
    _collect_model_entries,
    _normalize_use_for,
    validate_agent_runtime_config,
)


VALID_CONFIG = {
    "agent_runtime": {
        "service_variant": "legacy",
        "agent_model": "openai/gpt-4.1",
        "api_style": "responses",
    },
    "model_list": [
        {
            "model": "gpt-4.1-2025-04-14",
            "use_for": ["summary"],
        },
        {
            "model": "openai/gpt-4.1",
            "use_for": ["agent"],
        },
    ],
}


@pytest.mark.parametrize("service_variant", ["legacy", "refactored"])
def test_validate_agent_runtime_config_accepts_valid_runtime_config(
    service_variant,
):
    """正しい設定なら検証を通過することを確認する。"""
    config = {
        **VALID_CONFIG,
        "agent_runtime": {
            "service_variant": service_variant,
            "agent_model": "openai/gpt-4.1",
            "api_style": "responses",
        },
    }

    validate_agent_runtime_config(config)


@pytest.mark.completions_contract
def test_validate_agent_runtime_config_accepts_refactored_completions_api_style():
    """refactored + completions は Gate B の valid matrix に含まれることを確認する。"""
    config = {
        **VALID_CONFIG,
        "agent_runtime": {
            "service_variant": "refactored",
            "agent_model": "openai/gpt-4.1",
            "api_style": "completions",
        },
    }

    validate_agent_runtime_config(config)


@pytest.mark.parametrize(
    ("service_variant", "expected_message"),
    [("delegating", "Only legacy, refactored are valid")],
)
def test_validate_agent_runtime_config_rejects_unsupported_service_variant(
    service_variant,
    expected_message,
):
    """未対応の service_variant は拒否されることを確認する。"""
    config = {
        **VALID_CONFIG,
        "agent_runtime": {
            "service_variant": service_variant,
            "agent_model": "openai/gpt-4.1",
        },
    }

    with pytest.raises(InvalidAgentRuntimeConfigError, match=expected_message):
        validate_agent_runtime_config(config)


def test_validate_agent_runtime_config_rejects_missing_agent_model():
    """model_list に存在しない agent_model は拒否されることを確認する。"""
    config = {
        **VALID_CONFIG,
        "agent_runtime": {
            "service_variant": "legacy",
            "agent_model": "openai/gpt-4.1-not-configured",
        },
    }

    with pytest.raises(
        InvalidAgentRuntimeConfigError, match="not present in model_list"
    ):
        validate_agent_runtime_config(config)


def test_validate_agent_runtime_config_rejects_non_list_model_list():
    """model_list が list でなければ専用例外で拒否することを確認する。"""
    config = {
        **VALID_CONFIG,
        "model_list": "openai/gpt-4.1",
    }

    with pytest.raises(
        InvalidAgentRuntimeConfigError, match="model_list must be a list"
    ):
        validate_agent_runtime_config(config)


@pytest.mark.rollback_api_style
def test_validate_agent_runtime_config_rejects_legacy_completions_api_style():
    """legacy + completions は startup validation で明示的に拒否されることを確認する。"""
    config = {
        **VALID_CONFIG,
        "agent_runtime": {
            "service_variant": "legacy",
            "agent_model": "openai/gpt-4.1",
            "api_style": "completions",
        },
    }

    with pytest.raises(
        InvalidAgentRuntimeConfigError,
        match="not supported for service_variant=legacy",
    ):
        validate_agent_runtime_config(config)


def test_normalize_use_for_branches():
    """_normalize_use_for の None / str / list / その他 の分岐を網羅する。"""
    assert _normalize_use_for(None) == []
    assert _normalize_use_for("agent") == ["agent"]
    assert _normalize_use_for(["agent", "summary"]) == ["agent", "summary"]
    assert _normalize_use_for(42) == ["42"]


def test_collect_model_entries_non_mapping_fallback():
    """Mapping でないオブジェクトは属性アクセスで dict に変換されることを確認する。"""
    from types import SimpleNamespace

    obj = SimpleNamespace(model="openai/gpt-4.1", use_for=["agent"])
    entries = _collect_model_entries([obj])
    assert entries == [{"model": "openai/gpt-4.1", "use_for": ["agent"]}]


def test_validate_rejects_empty_agent_model():
    """agent_model が空文字列なら拒否されることを確認する。"""
    from services.chat.agent_runtime_config import AgentRuntimeConfig

    with patch(
        "services.chat.config_validator.resolve_agent_runtime_config",
        return_value=AgentRuntimeConfig(service_variant="legacy", agent_model=""),
    ):
        with pytest.raises(
            InvalidAgentRuntimeConfigError, match="agent_model must be configured"
        ):
            validate_agent_runtime_config({})


def test_validate_agent_runtime_config_rejects_unsupported_api_style():
    config = {
        **VALID_CONFIG,
        "agent_runtime": {
            "service_variant": "legacy",
            "agent_model": "openai/gpt-4.1",
            "api_style": "xml",
        },
    }

    with pytest.raises(
        InvalidAgentRuntimeConfigError,
        match="agent_runtime.api_style: xml is not supported",
    ):
        validate_agent_runtime_config(config)


def test_validate_agent_runtime_config_rejects_missing_runtime_matrix_entry():
    from services.chat.agent_runtime_config import AgentRuntimeConfig

    with (
        patch(
            "services.chat.config_validator.resolve_agent_runtime_config",
            return_value=AgentRuntimeConfig(
                service_variant="legacy",
                agent_model="openai/gpt-4.1",
                api_style="responses",
            ),
        ),
        patch("services.chat.config_validator.VALID_AGENT_RUNTIME_MATRIX", {}),
    ):
        with pytest.raises(
            InvalidAgentRuntimeConfigError,
            match="VALID_AGENT_RUNTIME_MATRIX is missing an entry",
        ):
            validate_agent_runtime_config({})
