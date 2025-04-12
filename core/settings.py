import os
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class RunApp(BaseModel):
    host: str = '127.0.0.1'
    port: int = 8000
    reload: bool = True


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
    traffic_lights_prefix: str = '/traffic-lights'
    traffic_lights_tag_static_properties: str = 'Traffic lights static properties'
    traffic_lights_tag_monitoring: str = 'Traffic lights monitoring'
    traffic_lights_tag_management: str = 'Traffic lights management'

    run_config_default: RunApp = RunApp()
    run_config_sdp: RunApp = RunApp(host='192.168.45.93', port=8001)

settings_db = SettingsDb()
settings = Settings()
