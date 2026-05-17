"""Runtime configuration via environment variables (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="UCE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/uce.db"
    jwt_secret: str = Field(default="dev-secret-change-me")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # Default LLM provider (used by /execute when the competency itself doesn't override)
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-6"

    # Comma-separated CORS origins. Use "*" for dev only.
    cors_origins: str = "*"

    # Bootstrap a default admin if no users exist (dev convenience).
    bootstrap_admin_email: str = "admin@uce.local"
    bootstrap_admin_password: str = "changeme"

    # File path for the JSON-lines audit sink (in addition to the DB).
    audit_log_file: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
