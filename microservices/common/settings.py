from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SEMS_", env_file=".env", extra="ignore")

    database_url: str = "sqlite://"
    jwt_secret: str = "dev-only-change-me-use-32b-plus!"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 480
    env: str = "development"
    service_name: str = "sems-r-service"
    bootstrap_admin: bool = False
    identity_url: str = "http://127.0.0.1:8000"
    faculty_url: str = "http://127.0.0.1:8001"
    student_url: str = "http://127.0.0.1:8002"
    grade_url: str = "http://127.0.0.1:8003"
    finance_url: str = "http://127.0.0.1:8004"
    attendance_url: str = "http://127.0.0.1:8005"
    library_url: str = "http://127.0.0.1:8006"
    http_keepalive: bool = True


@lru_cache
def service_settings() -> ServiceSettings:
    return ServiceSettings()


def peer_urls(settings: ServiceSettings | None = None) -> dict[str, str]:
    cfg = settings or service_settings()
    return {
        "identity": cfg.identity_url,
        "faculty": cfg.faculty_url,
        "student": cfg.student_url,
        "grade": cfg.grade_url,
        "finance": cfg.finance_url,
        "attendance": cfg.attendance_url,
        "library": cfg.library_url,
    }
