from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
    database_url: str = "postgresql+asyncpg://cvscreen:cvscreen@localhost:5432/cvscreen"
    gemini_api_key: str = ""
    gemini_chat_model: str = "gemini-flash-latest"
    gemini_embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768
    cv_directory: Path = Path("../data/cvs")
    auto_index: bool = False
    cors_origins: str = Field(default="http://localhost:5173")

    @property
    def origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
