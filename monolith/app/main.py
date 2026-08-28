from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import build_api_router, register_exception_handlers
from app.config import get_settings
from app.database import create_schema
from app.instrumentation import RequestContextMiddleware, install_runtime_instrumentation


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_schema()
    settings = get_settings()
    if settings.bootstrap_admin:
        _ensure_admin()
    yield


def _ensure_admin() -> None:
    from app.database import SessionLocal
    from app.models import User
    from app.models.enums import UserRole
    from app.security import hash_password

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "admin@sems-r.local").first()
        if existing is None:
            db.add(
                User(
                    email="admin@sems-r.local",
                    password_hash=hash_password("admin123"),
                    full_name="SEMS-R Administrator",
                    role=UserRole.ADMIN,
                )
            )
            db.commit()
    finally:
        db.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="SEMS-R: Reconstructed Legacy Education System",
        description=(
            "Controlled software reconstruction based on documented functional and "
            "architectural characteristics of the historical SEMS case study. "
            "This is not the original production SEMS source code."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(RequestContextMiddleware)
    install_runtime_instrumentation(settings.trace_path or None)
    register_exception_handlers(app)
    app.include_router(build_api_router())

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "system": settings.system_name,
            "integrity": "reconstruction_not_original_sems",
        }

    return app


app = create_app()
