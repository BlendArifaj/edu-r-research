from common.app import service_app
from student.api import internal, router
from student.deps import configure


def create_app(engine=None):
    configure(engine)
    app = service_app("SEMS-R student")
    app.include_router(router)
    app.include_router(internal)
    return app


app = create_app()
