"""API test fixtures — in-memory SQLite + fake LLM."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from uce_llm.base import LLMProvider, Message, Response, TokenUsage
from uce_llm.registry import register_provider


class _StubLLM(LLMProvider):
    """Deterministic LLM used in API tests so no network is needed."""

    name = "stub"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def complete(self, messages, **kwargs):  # type: ignore[override]
        text = messages[-1].content if messages else ""
        return Response(
            text=f"stub-reply: {text[:80]}",
            model=self.model,
            provider=self.name,
            usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2, cost_usd=0.0),
        )


# Register the stub under known names so the api/service layer picks it up.
register_provider("anthropic", _StubLLM)
register_provider("openai", _StubLLM)
register_provider("ollama", _StubLLM)


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    """Spin up a FastAPI client backed by a fresh SQLite DB per test."""
    db_path = tmp_path / "uce-test.db"
    monkeypatch.setenv("UCE_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("UCE_BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("UCE_BOOTSTRAP_ADMIN_PASSWORD", "adminpass123")
    monkeypatch.setenv("UCE_JWT_SECRET", "test-secret")

    # Reset cached settings + db engine since they read env at import time.
    from uce_api import config as cfg
    cfg.get_settings.cache_clear()

    import importlib
    from uce_api.db import session as session_mod
    importlib.reload(session_mod)
    from uce_api.db import init_db as init_mod
    importlib.reload(init_mod)
    from uce_api import auth as auth_mod
    importlib.reload(auth_mod)
    from uce_api import service as service_mod
    importlib.reload(service_mod)
    from uce_api.routers import auth as auth_router
    importlib.reload(auth_router)
    from uce_api.routers import competencies as comp_router
    importlib.reload(comp_router)
    from uce_api.routers import memory as mem_router
    importlib.reload(mem_router)
    from uce_api.routers import executions as exec_router
    importlib.reload(exec_router)
    from uce_api.routers import audit as audit_router
    importlib.reload(audit_router)
    from uce_api.routers import performance as perf_router
    importlib.reload(perf_router)
    from uce_api import main as main_mod
    importlib.reload(main_mod)

    with TestClient(main_mod.create_app()) as c:
        yield c


@pytest.fixture
def admin_token(client) -> str:
    r = client.post(
        "/auth/login",
        data={"username": "admin@example.com", "password": "adminpass123"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sample_definition() -> dict:
    return {
        "id": "demo",
        "name": "Demo Competency",
        "mission": "Echo things",
        "objectives": [{"id": "o1", "name": "Echo"}],
        "skills": [
            {
                "id": "echo",
                "name": "Echo",
                "execution_steps": [
                    {"id": "say", "type": "prompt", "prompt": "echo: {{inputs.text}}", "output_key": "msg"}
                ],
            }
        ],
        "workflows": [
            {
                "id": "main",
                "name": "Main",
                "is_default": True,
                "steps": [
                    {"id": "r", "type": "skill", "skill": "echo", "output_key": "msg"},
                ],
            }
        ],
        "policies": [
            {"id": "allow", "name": "Allow all", "effect": "allow", "applies_to": ["*"]}
        ],
        "llm": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
    }
