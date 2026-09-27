"""
Central configuration for DevPilot's backend.

Every value here is read from the environment (or `.env` in local dev) so
that secrets never end up hardcoded in source. See `.env.example` at the
repo root for the full list of variables.
"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the .env path relative to *this file*, not the process CWD.
# That means `uvicorn app.main:app` works correctly whether it is launched
# from devpilot/backend/, devpilot/, or anywhere else.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "DevPilot"
    environment: str = "development"
    cors_origins: str = "http://localhost:5173"

    # --- Database ---
    database_url: str = "postgresql+psycopg://devpilot:devpilot@localhost:5432/devpilot"

    # --- Workspaces ---
    # Absolute root directory that holds every project's isolated workspace.
    # The agent (in later phases) is only ever allowed to touch paths inside
    # workspaces_root/{project_id}/ — see app/services/sandbox/local.py.
    workspaces_root: str = str((Path(__file__).resolve().parent.parent.parent / "workspaces"))

    # --- LLM provider (used starting Phase 2) ---
    openai_api_key: str = "ollama"
    openai_model: str = "llama3.2:1b"
    openai_base_url: str = "http://localhost:11434/v1"

    # --- Agent limits (used starting Phase 2-4) ---
    agent_max_debug_iterations: int = 5
    command_timeout_seconds: int = 30
    max_output_bytes: int = 200_000

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
