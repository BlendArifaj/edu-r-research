from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas import (
    BookCopyIn,
    BookCopyOut,
    BookIn,
    BookOut,
    LibraryMemberIn,
    LibraryMemberOut,
    LoanIn,
    LoanOut,
    ReservationIn,
    ReservationOut,
)
from common.auth import require_user
from common.peers import get_peers
from library.deps import get_db
from library.service import LibraryService

router = APIRouter()
internal = APIRouter(prefix="/internal")


def _service(db: Session = Depends(get_db)) -> LibraryService:
    return LibraryService(db, get_peers())


@router.post("/api/v1/books", response_model=BookOut, status_code=201)
def create_book(payload: BookIn, _: dict = Depends(require_user), service: LibraryService = Depends(_service)):
    return service.create_book(payload)


@router.get("/api/v1/books", response_model=list[BookOut])
def search_books(
    q: str | None = None, _: dict = Depends(require_user), service: LibraryService = Depends(_service)
):
    return service.search_books(q)


@router.get("/api/v1/books/{book_id}", response_model=BookOut)
def get_book(book_id: int, _: dict = Depends(require_user), service: LibraryService = Depends(_service)):
    return service.get_book(book_id)


@router.post("/api/v1/books/{book_id}/copies", response_model=BookCopyOut, status_code=201)
def add_copy(
    book_id: int,
    payload: BookCopyIn,
    _: dict = Depends(require_user),
    service: LibraryService = Depends(_service),
):
    return service.add_copy(book_id, payload)


@router.get("/api/v1/books/{book_id}/copies", response_model=list[BookCopyOut])
def list_copies(
    book_id: int, _: dict = Depends(require_user), service: LibraryService = Depends(_service)
):
    return service.list_copies(book_id)


@router.post("/api/v1/library/members", response_model=LibraryMemberOut, status_code=201)
def create_member(
    payload: LibraryMemberIn, _: dict = Depends(require_user), service: LibraryService = Depends(_service)
):
    return service.create_member(payload)


@router.get("/api/v1/library/members/{member_id}", response_model=LibraryMemberOut)
def get_member(
    member_id: int, _: dict = Depends(require_user), service: LibraryService = Depends(_service)
):
    return service.get_member(member_id)


@router.post("/api/v1/library/loans", response_model=LoanOut, status_code=201)
def borrow_book(
    payload: LoanIn, _: dict = Depends(require_user), service: LibraryService = Depends(_service)
):
    return service.borrow(payload)


@router.post("/api/v1/library/loans/{loan_id}/return", response_model=LoanOut)
def return_book(
    loan_id: int, _: dict = Depends(require_user), service: LibraryService = Depends(_service)
):
    return service.return_loan(loan_id)


@router.get("/api/v1/library/members/{member_id}/loans", response_model=list[LoanOut])
def active_loans(
    member_id: int, _: dict = Depends(require_user), service: LibraryService = Depends(_service)
):
    return service.active_loans(member_id)


@router.post("/api/v1/library/reservations", response_model=ReservationOut, status_code=201)
def reserve_book(
    payload: ReservationIn, _: dict = Depends(require_user), service: LibraryService = Depends(_service)
):
    return service.reserve(payload)


@router.get("/api/v1/library/reservations", response_model=list[ReservationOut])
def list_reservations(
    member_id: int | None = None,
    _: dict = Depends(require_user),
    service: LibraryService = Depends(_service),
):
    return service.list_reservations(member_id)


@internal.get("/loans/count")
def internal_loan_count(
    user_id: int, _: dict = Depends(require_user), service: LibraryService = Depends(_service)
):
    return {"count": service.loans_for_user(user_id)}
