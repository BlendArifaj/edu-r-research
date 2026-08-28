from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import DomainError
from app.schemas import BookCopyIn, BookIn, LibraryMemberIn, LoanIn, ReservationIn
from common.http import Peers
from library.models import (
    Book,
    BookCopy,
    LibraryMember,
    Loan,
    Reservation,
    active_loan_count,
    member_by_user,
    require_book,
    require_copy,
    require_loan,
    require_member,
)


class LibraryService:
    def __init__(self, db: Session, peers: Peers) -> None:
        self.db = db
        self.peers = peers

    def create_book(self, data: BookIn) -> Book:
        book = Book(**data.model_dump())
        self.db.add(book)
        self.db.flush()
        return book

    def search_books(self, query: str | None = None) -> list[Book]:
        stmt = select(Book)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(Book.title.ilike(pattern) | Book.author.ilike(pattern))
        return list(self.db.scalars(stmt))

    def get_book(self, book_id: int) -> Book:
        return require_book(self.db, book_id)

    def add_copy(self, book_id: int, data: BookCopyIn) -> BookCopy:
        self.get_book(book_id)
        copy = BookCopy(book_id=book_id, barcode=data.barcode, location=data.location)
        self.db.add(copy)
        self.db.flush()
        return copy

    def list_copies(self, book_id: int) -> list[BookCopy]:
        book = self.get_book(book_id)
        return list(book.copies)

    def create_member(self, data: LibraryMemberIn) -> LibraryMember:
        self.peers.call("identity", "GET", f"/internal/users/{data.user_id}")
        if data.member_type == "student":
            found = self.peers.call("student", "GET", f"/internal/students/by-user/{data.user_id}")
            if found.get("id") is None:
                raise DomainError("student membership requires a student record")
        if data.member_type == "staff":
            staff_ids = self.peers.call("faculty", "GET", "/internal/staff-user-ids")
            if data.user_id not in staff_ids.get("user_ids", []):
                raise DomainError("staff membership requires a staff record")
        member = LibraryMember(
            user_id=data.user_id,
            member_number=data.member_number,
            member_type=data.member_type,
        )
        self.db.add(member)
        self.db.flush()
        return member

    def get_member(self, member_id: int) -> LibraryMember:
        return require_member(self.db, member_id)

    def borrow(self, data: LoanIn) -> Loan:
        member = self.get_member(data.member_id)
        self._assert_member_active(member)
        copy = require_copy(self.db, data.copy_id)
        if copy.status != "available":
            raise DomainError("copy is not available")
        now = datetime.now(UTC)
        copy.status = "on_loan"
        loan = Loan(
            copy_id=copy.id,
            member_id=member.id,
            borrowed_at=now,
            due_at=now + timedelta(days=data.days),
            status="active",
        )
        self.db.add(loan)
        self.db.flush()
        return loan

    def return_loan(self, loan_id: int) -> Loan:
        loan = require_loan(self.db, loan_id)
        if loan.status != "active":
            raise DomainError("loan is not active")
        loan.returned_at = datetime.now(UTC)
        loan.status = "returned"
        copy = require_copy(self.db, loan.copy_id)
        copy.status = "available"
        self.db.flush()
        return loan

    def active_loans(self, member_id: int) -> list[Loan]:
        self.get_member(member_id)
        return list(
            self.db.scalars(select(Loan).where(Loan.member_id == member_id, Loan.status == "active"))
        )

    def reserve(self, data: ReservationIn) -> Reservation:
        member = self.get_member(data.member_id)
        self._assert_member_active(member)
        book = self.get_book(data.book_id)
        row = Reservation(
            book_id=book.id,
            member_id=member.id,
            reserved_at=datetime.now(UTC),
            status="active",
        )
        self.db.add(row)
        self.db.flush()
        return row

    def list_reservations(self, member_id: int | None = None) -> list[Reservation]:
        stmt = select(Reservation)
        if member_id is not None:
            stmt = stmt.where(Reservation.member_id == member_id)
        return list(self.db.scalars(stmt))

    def loans_for_user(self, user_id: int) -> int:
        member = member_by_user(self.db, user_id)
        if member is None:
            return 0
        return active_loan_count(self.db, member.id)

    def _assert_member_active(self, member: LibraryMember) -> None:
        if member.member_type != "student":
            return
        found = self.peers.call("student", "GET", f"/internal/students/by-user/{member.user_id}")
        if found.get("id") is None or found.get("status") != "active":
            raise DomainError("inactive students cannot borrow or reserve")
