import time
from collections.abc import Callable, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from common.settings import service_settings


def make_engine(url: str | None = None, *, echo: bool = False):
    database_url = url or service_settings().database_url
    connect_args = {}
    kwargs: dict = {"future": True, "echo": echo}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if database_url == "sqlite://":
            kwargs["poolclass"] = StaticPool
    kwargs["connect_args"] = connect_args
    return create_engine(database_url, **kwargs)


def wait_for_database(engine, attempts: int = 30, delay_seconds: float = 1.0) -> None:
    last: BaseException | None = None
    for _ in range(attempts):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except OperationalError as exc:
            last = exc
            time.sleep(delay_seconds)
    raise last if last is not None else RuntimeError("database did not become ready")


def create_schema(base, engine, attempts: int = 30, delay_seconds: float = 0.2) -> None:
    """create_all with retries so two replicas can start against one empty database."""
    last: BaseException | None = None
    for _ in range(attempts):
        try:
            base.metadata.create_all(bind=engine)
            return
        except (IntegrityError, OperationalError, ProgrammingError) as exc:
            last = exc
            time.sleep(delay_seconds)
    raise last if last is not None else RuntimeError("schema create failed")


def session_factory(engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def db_dependency(factory: sessionmaker[Session]) -> Callable[[], Generator[Session, None, None]]:
    def get_db() -> Generator[Session, None, None]:
        db = factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return get_db
