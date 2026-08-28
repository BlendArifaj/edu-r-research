from common.app import service_app
from faculty.api import internal, router
from faculty.deps import configure


def create_app(engine=None):
    configure(engine)
    app = service_app("SEMS-R faculty")
    app.include_router(router)
    app.include_router(internal)
    return app


app = create_app()
