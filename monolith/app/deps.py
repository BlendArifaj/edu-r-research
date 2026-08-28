from collections.abc import Generator
from contextvars import ContextVar
from uuid import uuid4

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import AuthorizationError
from app.models import User
from app.repositories import UserRepository
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def current_request_id() -> str:
    return request_id_ctx.get()


def get_request_id(x_request_id: str | None = Header(default=None, alias="X-Request-ID")) -> str:
    value = x_request_id or str(uuid4())
    request_id_ctx.set(value)
    return value


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthorizationError("authentication required")
    payload = decode_access_token(credentials.credentials)
    return UserRepository(db).get(int(payload["user_id"]))


def db_session(db: Session = Depends(get_db)) -> Generator[Session, None, None]:
    yield db
