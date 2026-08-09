# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

AI career advisor agent server ("AICA Agent") for MIIDAS — a Japanese job-change platform. The system exposes a WebSocket endpoint for LLM-driven career conversations and REST endpoints for position search/detail. It is organized as three independent Python packages:

- **`server/`** — FastAPI + WebSocket server (main agent logic)
- **`cli/`** — Typer batch CLI (session cleanup, rate-limit aggregation)
- **`e2e/`** — headless WebSocket client for end-to-end testing

Python 3.14 is required (`>=3.14,<3.15`) across all three packages.

---

## Commands

### Server

#### How run test locally

```bash
# Run all tests
OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/

# Run a single test file
OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/unit/test_websocket_endpoint.py

# Run a single test function
OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/unit/services/test_chat_service.py::TestLoadPreviousChatHistories::test_respects_limit_parameter
```
