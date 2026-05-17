"""FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from uce_api.config import get_settings
from uce_api.db.init_db import init_database
from uce_api.routers import audit as audit_router
from uce_api.routers import auth as auth_router
from uce_api.routers import competencies as comp_router
from uce_api.routers import executions as exec_router
from uce_api.routers import health as health_router
from uce_api.routers import memory as memory_router
from uce_api.routers import performance as perf_router


@asynccontextmanager
async def _lifespan(app: FastAPI):
    init_database()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Universal Competency Engine",
        version="0.1.0",
        description="Author, run, govern, and evaluate AI competencies — provider-agnostic.",
        lifespan=_lifespan,
    )
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router.router)
    app.include_router(auth_router.router)
    app.include_router(comp_router.router)
    app.include_router(memory_router.router)
    app.include_router(exec_router.router)
    app.include_router(audit_router.router)
    app.include_router(perf_router.router)
    return app


app = create_app()
