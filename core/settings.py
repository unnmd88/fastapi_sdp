import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class SettingsDb(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    POSTGRES_DB: str

    echo: bool = True
    pool_size: int = 5

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_db_url(self):
        return (f"postgresql+asyncpg://"
                f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}")


class Settings(BaseSettings):
    api_v1_prefix: str = '/api/v1'
    traffic_lights_tag_static_properties: str = 'Traffic lights static properties'
    traffic_lights_tag_monitoring: str = 'Traffic lights monitoring'
    traffic_lights_tag_management: str = 'Traffic lights management'


settings_db = SettingsDb()
settings = Settings()
