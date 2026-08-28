from common.app import service_app
from library.api import internal, router
from library.deps import configure


def create_app(engine=None):
    configure(engine)
    app = service_app("SEMS-R library")
    app.include_router(router)
    app.include_router(internal)
    return app


app = create_app()
