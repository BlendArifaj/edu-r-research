from contextlib import asynccontextmanager

from fastapi import FastAPI

from common.app import service_app
from common.settings import service_settings
from identity.api import internal_router, public_router
from identity.deps import configure
from identity.models import ensure_admin


def create_app(engine=None) -> FastAPI:
    settings = service_settings()
    _, factory = configure(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if settings.bootstrap_admin:
            db = factory()
            try:
                ensure_admin(db)
            finally:
                db.close()
        yield

    app = service_app("SEMS-R identity", lifespan=lifespan)
    app.include_router(public_router)
    app.include_router(internal_router)
    return app


app = create_app()
