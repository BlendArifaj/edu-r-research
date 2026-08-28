from collections.abc import Generator

from sqlalchemy.orm import Session

from common.db import db_dependency, make_engine, session_factory, wait_for_database
from identity.models import Base

_get_db = None


def configure(engine=None):
    engine = engine or make_engine()
    wait_for_database(engine)
    Base.metadata.create_all(bind=engine)
    factory = session_factory(engine)
    global _get_db
    _get_db = db_dependency(factory)
    return engine, factory


def get_db() -> Generator[Session, None, None]:
    if _get_db is None:
        configure()
    assert _get_db is not None
    yield from _get_db()
