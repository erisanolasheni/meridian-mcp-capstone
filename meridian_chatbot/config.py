from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    mcp_url: str = "https://order-mcp-74afyau24q-uc.a.run.app/mcp"
    mcp_timeout: float = Field(default=30.0, ge=1.0)
    mcp_sse_read_timeout: float = Field(default=120.0, ge=5.0)

    openai_api_key: SecretStr | None = Field(default=None, validation_alias=AliasChoices("OPENAI_API_KEY"))
    llm_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("LLM_MODEL", "OPENAI_MODEL"),
    )
    llm_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LLM_BASE_URL", "OPENAI_BASE_URL"),
    )

    max_tool_rounds: int = Field(default=12, ge=1, le=32)
    history_max_messages: int = Field(default=24, ge=2)


@lru_cache
def get_settings() -> Settings:
    return Settings()
