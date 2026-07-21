from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "app-service"
    version: str = "0.1.0"
    environment: str = "local"
    log_level: str = "INFO"
    request_timeout_seconds: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()