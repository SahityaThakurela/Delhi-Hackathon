from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    REDIS_URL: str = "redis://localhost:6379/0"

    S3_ENDPOINT: Optional[str] = None
    S3_BUCKET: str = "kyro-documents"
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_REGION: str = "ap-south-1"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_CHAT_MODEL: str = "gpt-4o"
    OPENAI_FAST_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBED_MODEL: str = "text-embedding-3-large"
    EMBED_DIMENSIONS: int = 1536

    JWT_SECRET: str = "kyro-insecure-secret-for-dev-only-change-in-prod"
    JWT_ACCESS_MINUTES: int = 60
    JWT_REFRESH_DAYS: int = 7

    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]
    NVD_API_KEY: Optional[str] = None
    NCBI_API_KEY: Optional[str] = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()
