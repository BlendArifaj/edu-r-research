from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SEMS_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./sems_r.db"
    jwt_secret: str = "dev-only-change-me-use-32b-plus!"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 480
    env: str = "development"
    system_name: str = "SEMS-R"
    trace_path: str = ""
    trace_enabled: bool = True
    bootstrap_admin: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
