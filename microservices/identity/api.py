from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.exceptions import AuthorizationError
from app.schemas import LoginRequest, TokenResponse, UserOut
from app.security import create_access_token, hash_password, verify_password
from common.auth import require_user
from identity.deps import get_db
from identity.models import User, add_user, get_by_email, get_user

public_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
internal_router = APIRouter(prefix="/internal/users", tags=["identity-internal"])


class UserCreateIn(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "student"


class UserPatchIn(BaseModel):
    full_name: str | None = None
    role: str | None = None


@public_router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = get_by_email(db, payload.email)
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise AuthorizationError("invalid credentials")
    return TokenResponse(access_token=create_access_token(user.id, user.role))


@public_router.get("/me", response_model=UserOut)
def me(current: dict[str, str] = Depends(require_user), db: Session = Depends(get_db)) -> User:
    return get_user(db, int(current["user_id"]))


@internal_router.post("", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreateIn,
    _: dict[str, str] = Depends(require_user),
    db: Session = Depends(get_db),
) -> User:
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    return add_user(db, user)


@internal_router.get("/{user_id}", response_model=UserOut)
def read_user(
    user_id: int,
    _: dict[str, str] = Depends(require_user),
    db: Session = Depends(get_db),
) -> User:
    return get_user(db, user_id)


@internal_router.patch("/{user_id}", response_model=UserOut)
def patch_user(
    user_id: int,
    payload: UserPatchIn,
    _: dict[str, str] = Depends(require_user),
    db: Session = Depends(get_db),
) -> User:
    user = get_user(db, user_id)
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role
    db.flush()
    return user
