from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.exceptions import NotFoundError
from common.models import PrimaryKeyMixin, TimestampMixin, make_base

Base = make_base()


class Book(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "books"

    isbn: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    copies: Mapped[list["BookCopy"]] = relationship(back_populates="book")


class BookCopy(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "book_copies"

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    barcode: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="available", nullable=False)
    location: Mapped[str] = mapped_column(String(64), nullable=False, default="main")

    book: Mapped[Book] = relationship(back_populates="copies")
    loans: Mapped[list["Loan"]] = relationship(back_populates="copy")


class LibraryMember(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "library_members"

    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    member_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    member_type: Mapped[str] = mapped_column(String(32), default="student", nullable=False)

    loans: Mapped[list["Loan"]] = relationship(back_populates="member")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="member")


class Loan(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "loans"

    copy_id: Mapped[int] = mapped_column(ForeignKey("book_copies.id"), nullable=False, index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("library_members.id"), nullable=False, index=True)
    borrowed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    copy: Mapped[BookCopy] = relationship(back_populates="loans")
    member: Mapped[LibraryMember] = relationship(back_populates="loans")


class Reservation(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reservations"

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("library_members.id"), nullable=False, index=True)
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    member: Mapped[LibraryMember] = relationship(back_populates="reservations")

    __table_args__ = (UniqueConstraint("book_id", "member_id", "status", name="uq_active_reservation"),)


def require_book(db: Session, book_id: int) -> Book:
    row = db.get(Book, book_id)
    if row is None:
        raise NotFoundError("Book", book_id)
    return row


def require_copy(db: Session, copy_id: int) -> BookCopy:
    row = db.get(BookCopy, copy_id)
    if row is None:
        raise NotFoundError("BookCopy", copy_id)
    return row


def require_member(db: Session, member_id: int) -> LibraryMember:
    row = db.get(LibraryMember, member_id)
    if row is None:
        raise NotFoundError("LibraryMember", member_id)
    return row


def require_loan(db: Session, loan_id: int) -> Loan:
    row = db.get(Loan, loan_id)
    if row is None:
        raise NotFoundError("Loan", loan_id)
    return row


def member_by_user(db: Session, user_id: int) -> LibraryMember | None:
    return db.scalar(select(LibraryMember).where(LibraryMember.user_id == user_id))


def active_loan_count(db: Session, member_id: int) -> int:
    value = db.scalar(
        select(func.count()).select_from(Loan).where(Loan.member_id == member_id, Loan.status == "active")
    )
    return int(value or 0)
