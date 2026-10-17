"""
Application configuration sourced from environment variables / backend/.env.

Uses pydantic-settings; every variable in .env.example is declared here so
missing values are caught at startup rather than at request time.
"""
from __future__ import annotations

import os
from pathlib import Path

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env path relative to this file regardless of cwd
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str  # postgresql+asyncpg://...

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = ""

    # ── S3 / Storage ──────────────────────────────────────────────────────────
    S3_ENDPOINT: str = ""
    S3_BUCKET: str = "kyro-documents"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_REGION: str = "ap-south-1"

    # ── OpenAI ────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_CHAT_MODEL: str = "gpt-4o"
    OPENAI_FAST_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBED_MODEL: str = "text-embedding-3-large"
    EMBED_DIMENSIONS: int = 1536

    # ── Auth ──────────────────────────────────────────────────────────────────
    JWT_SECRET: str
    JWT_ACCESS_MINUTES: int = 60
    JWT_REFRESH_DAYS: int = 7

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ── Optional external APIs ────────────────────────────────────────────────
    NVD_API_KEY: str = ""
    NCBI_API_KEY: str = ""

    # ── Demo ──────────────────────────────────────────────────────────────────
    DEMO_PASSWORD: str = "kyro-demo-2026"


settings = Settings()
