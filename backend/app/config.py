from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Backend-only settings. Secrets should never be sent to the frontend."""

    ollama_base_url: str = "http://localhost:11434"
    huggingface_api_key: str = Field(default="", repr=False)
    nvidia_api_key: str = Field(default="", repr=False)
    database_path: Path = Path("data/arena.sqlite3")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def huggingface_configured(self) -> bool:
        return bool(self.huggingface_api_key.strip())

    @property
    def nvidia_configured(self) -> bool:
        return bool(self.nvidia_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
