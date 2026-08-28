from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin
from app.models.enums import CopyStatus, LoanStatus, MemberType, ReservationStatus


class Book(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "books"

    isbn: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    copies: Mapped[list["BookCopy"]] = relationship(back_populates="book")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="book")


class BookCopy(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "book_copies"

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    barcode: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=CopyStatus.AVAILABLE, nullable=False)
    location: Mapped[str] = mapped_column(String(64), nullable=False, default="main")

    book: Mapped[Book] = relationship(back_populates="copies")
    loans: Mapped[list["Loan"]] = relationship(back_populates="copy")


class LibraryMember(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "library_members"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    member_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    member_type: Mapped[str] = mapped_column(String(32), default=MemberType.STUDENT, nullable=False)

    user: Mapped["User"] = relationship(back_populates="library_member")
    loans: Mapped[list["Loan"]] = relationship(back_populates="member")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="member")


class Loan(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "loans"

    copy_id: Mapped[int] = mapped_column(ForeignKey("book_copies.id"), nullable=False, index=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("library_members.id"), nullable=False, index=True
    )
    borrowed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=LoanStatus.ACTIVE, nullable=False)

    copy: Mapped[BookCopy] = relationship(back_populates="loans")
    member: Mapped[LibraryMember] = relationship(back_populates="loans")


class Reservation(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reservations"

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("library_members.id"), nullable=False, index=True
    )
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ReservationStatus.ACTIVE, nullable=False
    )

    book: Mapped[Book] = relationship(back_populates="reservations")
    member: Mapped[LibraryMember] = relationship(back_populates="reservations")

    __table_args__ = (
        UniqueConstraint("book_id", "member_id", "status", name="uq_active_reservation"),
    )
