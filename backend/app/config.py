from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    search_provider: Literal["mock", "exa", "tavily"] = "mock"
    llm_provider: Literal["mock", "openai", "nightshift"] = "mock"
    exa_api_key: str | None = None
    tavily_api_key: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    nightshift_base_url: str = "http://127.0.0.1:8088/v1"
    nightshift_api_key: str | None = None
    nightshift_model: str = "meterless/auto"
    meterless_app: str = "meetmind"
    zetaris_rest_url: str = "http://localhost:8888/api/v1.0"
    zetaris_base_url: str | None = None
    zetaris_org_id: str | None = None
    zetaris_api_key: str | None = None
    cors_origins: str = "http://localhost:3010,http://127.0.0.1:3010"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator(
        "exa_api_key",
        "tavily_api_key",
        "openai_api_key",
        "nightshift_api_key",
        "zetaris_api_key",
        "zetaris_org_id",
        "zetaris_base_url",
        mode="before",
    )
    @classmethod
    def blank_api_key_is_unset(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
