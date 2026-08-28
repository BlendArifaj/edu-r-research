from attendance.api import internal, router
from attendance.deps import configure
from common.app import service_app


def create_app(engine=None):
    configure(engine)
    app = service_app("SEMS-R attendance")
    app.include_router(router)
    app.include_router(internal)
    return app


app = create_app()
