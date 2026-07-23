from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RETRIVAL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "retrieval-service"
    version: str = "0.1.0"
    environment: str = "local"
    log_level: str = "INFO"
    # Where Chroma persists. Relative to the service; gitignored already.
    chroma_path: str = "data/chroma"
    collection_name: str = "askdocs"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    


@lru_cache  # parse env/.env exactly once per process, not per call
def get_settings() -> Settings:
    return Settings()