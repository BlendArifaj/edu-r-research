from sqlalchemy import Boolean, String, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.exceptions import ConflictError, NotFoundError
from app.security import hash_password
from common.models import PrimaryKeyMixin, TimestampMixin, make_base

BOOTSTRAP_ADMIN_EMAIL = "admin@sems-r.local"

Base = make_base()


class User(PrimaryKeyMixin, TimestampMixin, Base):
    """Gateway-owned identity. Not assigned to one of the six historical services."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="student", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User", user_id)
    return user


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def ensure_admin(db: Session) -> None:
    """Idempotent admin row so gateway replicas can start together."""
    if get_by_email(db, BOOTSTRAP_ADMIN_EMAIL) is not None:
        return
    db.add(
        User(
            email=BOOTSTRAP_ADMIN_EMAIL,
            password_hash=hash_password("admin123"),
            full_name="SEMS-R Administrator",
            role="admin",
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()


def add_user(db: Session, user: User) -> User:
    if get_by_email(db, user.email) is not None:
        raise ConflictError("email already registered")
    db.add(user)
    db.flush()
    return user
