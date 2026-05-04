"""Typed application settings, sourced from environment + .env file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3].parent
ENV_FILES = (REPO_ROOT / ".env", Path.cwd() / ".env")


class Settings(BaseSettings):
    """Single source of truth for runtime configuration.

    Values are loaded from (in order): process env, ``.env`` at repo root,
    ``.env`` in cwd. Anything missing falls back to the defaults below.
    """

    model_config = SettingsConfigDict(
        env_file=tuple(str(p) for p in ENV_FILES),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_env: Literal["development", "production", "test"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_allowed_origins: str = "http://localhost:3000"

    # --- LLM ---
    llm_provider: Literal["groq", "openai", "anthropic", "ollama"] = "groq"
    groq_api_key: SecretStr | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-haiku-4-5-20251001"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # --- Embeddings ---
    embedding_provider: Literal["local", "openai"] = "local"
    embedding_model_local: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384

    # --- Database ---
    database_url: str = "postgresql+psycopg://changetools:changetools@localhost:5432/changetools"

    # --- Object storage (Cloudflare R2 / S3-compatible) ---
    r2_account_id: str = ""
    r2_access_key_id: SecretStr | None = None
    r2_secret_access_key: SecretStr | None = None
    r2_bucket: str = "changetools-uploads"
    r2_endpoint: str = ""
    r2_public_base_url: str = ""

    # --- Tracing ---
    langchain_tracing_v2: bool = False
    langchain_api_key: SecretStr | None = None
    langchain_project: str = "changetools-obsidian"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    # --- Validators ---
    @field_validator("cors_allowed_origins")
    @classmethod
    def _strip_whitespace(cls, v: str) -> str:
        return v.strip()

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    def llm_credentials_present(self) -> bool:
        """Whether the configured LLM provider has the credentials it needs."""
        match self.llm_provider:
            case "groq":
                return self.groq_api_key is not None
            case "openai":
                return self.openai_api_key is not None
            case "anthropic":
                return self.anthropic_api_key is not None
            case "ollama":
                return True
        return False  # pragma: no cover - exhausted match


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide settings cache. Reset with ``get_settings.cache_clear()`` in tests."""
    return Settings()
