from common.app import service_app
from finance.api import internal, router
from finance.deps import configure


def create_app(engine=None):
    configure(engine)
    app = service_app("SEMS-R finance")
    app.include_router(router)
    app.include_router(internal)
    return app


app = create_app()
