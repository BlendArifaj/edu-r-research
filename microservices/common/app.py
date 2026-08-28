from typing import Any

from fastapi import FastAPI

from common.errors import register_exception_handlers
from common.middleware import ForwardAuthMiddleware
from common.settings import service_settings


def service_app(title: str, lifespan: Any = None) -> FastAPI:
    settings = service_settings()
    kwargs: dict[str, Any] = {
        "title": title,
        "description": (
            "SEMS-R microservice reconstruction. Not the original production SEMS source. "
            "Separate logical database ownership; peers are reached over HTTP."
        ),
        "version": "0.1.0",
    }
    if lifespan is not None:
        kwargs["lifespan"] = lifespan
    app = FastAPI(**kwargs)
    app.add_middleware(ForwardAuthMiddleware)
    register_exception_handlers(app)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "system": "SEMS-R",
            "service": settings.service_name,
            "integrity": "reconstruction_not_original_sems",
        }

    return app
