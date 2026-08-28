from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import Book, BookCopy, LibraryMember, Loan, Reservation
from app.models.enums import CopyStatus, LoanStatus, ReservationStatus


class LibraryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_book(self, book: Book) -> Book:
        self.db.add(book)
        self.db.flush()
        return book

    def get_book(self, book_id: int) -> Book:
        book = self.db.get(Book, book_id)
        if book is None:
            raise NotFoundError("Book", book_id)
        return book

    def search_books(self, query: str | None = None) -> list[Book]:
        stmt = select(Book)
        if query:
            like = f"%{query}%"
            stmt = stmt.where(or_(Book.title.ilike(like), Book.author.ilike(like), Book.isbn.ilike(like)))
        return list(self.db.scalars(stmt.order_by(Book.id)).all())

    def add_copy(self, copy: BookCopy) -> BookCopy:
        self.db.add(copy)
        self.db.flush()
        return copy

    def get_copy(self, copy_id: int) -> BookCopy:
        copy = self.db.get(BookCopy, copy_id)
        if copy is None:
            raise NotFoundError("BookCopy", copy_id)
        return copy

    def available_copies(self, book_id: int) -> list[BookCopy]:
        stmt = select(BookCopy).where(
            BookCopy.book_id == book_id, BookCopy.status == CopyStatus.AVAILABLE
        )
        return list(self.db.scalars(stmt).all())

    def add_member(self, member: LibraryMember) -> LibraryMember:
        self.db.add(member)
        self.db.flush()
        return member

    def get_member(self, member_id: int) -> LibraryMember:
        member = self.db.get(LibraryMember, member_id)
        if member is None:
            raise NotFoundError("LibraryMember", member_id)
        return member

    def get_member_by_user(self, user_id: int) -> LibraryMember | None:
        return self.db.scalar(select(LibraryMember).where(LibraryMember.user_id == user_id))

    def add_loan(self, loan: Loan) -> Loan:
        self.db.add(loan)
        self.db.flush()
        return loan

    def get_loan(self, loan_id: int) -> Loan:
        loan = self.db.get(Loan, loan_id)
        if loan is None:
            raise NotFoundError("Loan", loan_id)
        return loan

    def active_loans(self, member_id: int) -> list[Loan]:
        stmt = select(Loan).where(Loan.member_id == member_id, Loan.status == LoanStatus.ACTIVE)
        return list(self.db.scalars(stmt).all())

    def add_reservation(self, reservation: Reservation) -> Reservation:
        self.db.add(reservation)
        self.db.flush()
        return reservation

    def list_reservations(self, member_id: int | None = None) -> list[Reservation]:
        stmt = select(Reservation).where(Reservation.status == ReservationStatus.ACTIVE)
        if member_id is not None:
            stmt = stmt.where(Reservation.member_id == member_id)
        return list(self.db.scalars(stmt.order_by(Reservation.id)).all())
