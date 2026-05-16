from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_TITLE: str = "Travel Planner API"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite:///./travel_planner.db"
    ARTIC_API_URL: str = "https://api.artic.edu/api/v1/artworks"
    ARTIC_TIMEOUT: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
