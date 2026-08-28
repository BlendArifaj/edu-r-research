from collections.abc import Generator
from typing import Any

from sqlalchemy.orm import Session

from common.db import create_schema, db_dependency, make_engine, session_factory, wait_for_database


class EngineBinder:
    def __init__(self, base: Any) -> None:
        self.base = base
        self._get_db = None
        self.factory = None
        self.engine = None

    def configure(self, engine=None):
        self.engine = engine or make_engine()
        wait_for_database(self.engine)
        create_schema(self.base, self.engine)
        self.factory = session_factory(self.engine)
        self._get_db = db_dependency(self.factory)
        return self.engine, self.factory

    def get_db(self) -> Generator[Session, None, None]:
        if self._get_db is None:
            self.configure()
        assert self._get_db is not None
        yield from self._get_db()
