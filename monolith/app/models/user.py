from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin
from app.models.enums import UserRole


class User(PrimaryKeyMixin, TimestampMixin, Base):
    """Shared identity table. Not assigned to a single historical domain service."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default=UserRole.STUDENT, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    student: Mapped["Student | None"] = relationship(back_populates="user", uselist=False)
    staff: Mapped["Staff | None"] = relationship(back_populates="user", uselist=False)
    library_member: Mapped["LibraryMember | None"] = relationship(
        back_populates="user", uselist=False
    )
