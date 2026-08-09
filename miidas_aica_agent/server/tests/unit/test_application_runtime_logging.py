from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import application


@pytest.mark.asyncio
async def test_lifespan_emits_startup_runtime_config_log(monkeypatch):
    """FastAPI startup path emits the Phase 6 runtime config log."""
    fake_config = {
        "agent_runtime": {
            "service_variant": "refactored",
            "agent_model": "openai/gpt-4.1",
        },
        "model_list": [{"model": "summary-model", "use_for": ["summary"]}],
    }
    fake_container = SimpleNamespace(
        config=fake_config,
        init_resources=AsyncMock(),
        shutdown_resources=AsyncMock(),
    )
    fake_loop = SimpleNamespace(
        get_exception_handler=Mock(return_value=None),
        set_exception_handler=Mock(),
    )

    monkeypatch.setattr(application, "container", fake_container)
    monkeypatch.setattr(application, "validate_agent_runtime_config", Mock())
    monkeypatch.setattr(application, "startup_poller", AsyncMock())
    monkeypatch.setattr(application, "shutdown_poller", AsyncMock())
    monkeypatch.setattr(
        application.asyncio, "get_running_loop", Mock(return_value=fake_loop)
    )
    info_mock = Mock()
    monkeypatch.setattr(application.logger, "info", info_mock)

    async with application.lifespan(None):
        pass

    application.validate_agent_runtime_config.assert_called_once_with(fake_config)
    info_mock.assert_any_call(
        "startup runtime config: service_variant=%s agent_model=%s summary_model=%s backend=%s",
        "refactored",
        "openai/gpt-4.1",
        "summary-model",
        "responses",
    )
