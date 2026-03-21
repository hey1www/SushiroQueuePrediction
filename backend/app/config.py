from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "sqlite:///./data/sushiro_hk.db"
    collect_interval_seconds: int = 120
    request_timeout_seconds: int = 15
    storelist_url: str = (
        "https://sushipass.sushiro.com.hk/api/2.0/info/storelist"
        "?latitude=22&longitude=114&numresults=25&region=HK"
    )
    groupqueues_url_template: str = (
        "https://sushipass.sushiro.com.hk/api/2.0/remote/groupqueues"
        "?region=HK&storeid={store_id}"
    )
    cors_allow_origins: list[str] = ["http://localhost:5173"]
    eta_alpha: float = 0.8
    eta_min_rate: float = 0.1
    eta_max_minutes: int = 180
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
