from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.exceptions import DomainError
from app.models import Book, BookCopy, LibraryMember, Loan, Reservation
from app.models.enums import CopyStatus, LoanStatus, MemberType, ReservationStatus, StudentStatus
from app.repositories import LibraryRepository, StaffRepository, StudentRepository, UserRepository
from app.schemas import BookCopyIn, BookIn, LibraryMemberIn, LoanIn, ReservationIn


class LibraryService:
    """Library membership is issued to students and staff; borrow checks student status."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.library = LibraryRepository(db)
        self.users = UserRepository(db)
        self.students = StudentRepository(db)
        self.staff_repo = StaffRepository(db)

    def create_book(self, data: BookIn) -> Book:
        return self.library.add_book(Book(**data.model_dump()))

    def search_books(self, query: str | None = None) -> list[Book]:
        return self.library.search_books(query)

    def get_book(self, book_id: int) -> Book:
        return self.library.get_book(book_id)

    def add_copy(self, book_id: int, data: BookCopyIn) -> BookCopy:
        self.library.get_book(book_id)
        return self.library.add_copy(
            BookCopy(book_id=book_id, barcode=data.barcode, location=data.location)
        )

    def list_copies(self, book_id: int) -> list[BookCopy]:
        book = self.library.get_book(book_id)
        return list(book.copies)

    def create_member(self, data: LibraryMemberIn) -> LibraryMember:
        user = self.users.get(data.user_id)
        if data.member_type == MemberType.STUDENT and self.students.get_by_user_id(user.id) is None:
            raise DomainError("student membership requires a student record")
        if data.member_type == MemberType.STAFF:
            staff_ids = {row.user_id for row in self.staff_repo.list()}
            if user.id not in staff_ids:
                raise DomainError("staff membership requires a staff record")
        return self.library.add_member(
            LibraryMember(
                user_id=user.id,
                member_number=data.member_number,
                member_type=data.member_type,
            )
        )

    def get_member(self, member_id: int) -> LibraryMember:
        return self.library.get_member(member_id)

    def borrow(self, data: LoanIn) -> Loan:
        member = self.library.get_member(data.member_id)
        self._assert_member_active(member)
        copy = self.library.get_copy(data.copy_id)
        if copy.status != CopyStatus.AVAILABLE:
            raise DomainError("copy is not available")
        now = datetime.now(UTC)
        copy.status = CopyStatus.ON_LOAN
        return self.library.add_loan(
            Loan(
                copy_id=copy.id,
                member_id=member.id,
                borrowed_at=now,
                due_at=now + timedelta(days=data.days),
                status=LoanStatus.ACTIVE,
            )
        )

    def return_loan(self, loan_id: int) -> Loan:
        loan = self.library.get_loan(loan_id)
        if loan.status != LoanStatus.ACTIVE:
            raise DomainError("loan is not active")
        loan.returned_at = datetime.now(UTC)
        loan.status = LoanStatus.RETURNED
        loan.copy.status = CopyStatus.AVAILABLE
        self.db.flush()
        return loan

    def active_loans(self, member_id: int) -> list[Loan]:
        self.library.get_member(member_id)
        return self.library.active_loans(member_id)

    def reserve(self, data: ReservationIn) -> Reservation:
        member = self.library.get_member(data.member_id)
        self._assert_member_active(member)
        book = self.library.get_book(data.book_id)
        return self.library.add_reservation(
            Reservation(
                book_id=book.id,
                member_id=member.id,
                reserved_at=datetime.now(UTC),
                status=ReservationStatus.ACTIVE,
            )
        )

    def list_reservations(self, member_id: int | None = None) -> list[Reservation]:
        return self.library.list_reservations(member_id)

    def _assert_member_active(self, member: LibraryMember) -> None:
        if member.member_type != MemberType.STUDENT:
            return
        student = self.students.get_by_user_id(member.user_id)
        if student is None or student.status != StudentStatus.ACTIVE:
            raise DomainError("inactive students cannot borrow or reserve")
