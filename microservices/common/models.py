from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def make_base() -> type[DeclarativeBase]:
    class Base(DeclarativeBase):
        pass

    return Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PrimaryKeyMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
