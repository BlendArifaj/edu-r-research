from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
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
from app.services import LibraryService

router = APIRouter(tags=["library"])


def _library(db: Session = Depends(get_db)) -> LibraryService:
    return LibraryService(db)


@router.post("/books", response_model=BookOut, status_code=201)
def create_book(
    payload: BookIn, _: User = Depends(get_current_user), service: LibraryService = Depends(_library)
):
    return service.create_book(payload)


@router.get("/books", response_model=list[BookOut])
def search_books(
    q: str | None = None,
    _: User = Depends(get_current_user),
    service: LibraryService = Depends(_library),
):
    return service.search_books(q)


@router.get("/books/{book_id}", response_model=BookOut)
def get_book(
    book_id: int, _: User = Depends(get_current_user), service: LibraryService = Depends(_library)
):
    return service.get_book(book_id)


@router.post("/books/{book_id}/copies", response_model=BookCopyOut, status_code=201)
def add_copy(
    book_id: int,
    payload: BookCopyIn,
    _: User = Depends(get_current_user),
    service: LibraryService = Depends(_library),
):
    return service.add_copy(book_id, payload)


@router.get("/books/{book_id}/copies", response_model=list[BookCopyOut])
def list_copies(
    book_id: int, _: User = Depends(get_current_user), service: LibraryService = Depends(_library)
):
    return service.list_copies(book_id)


@router.post("/library/members", response_model=LibraryMemberOut, status_code=201)
def create_member(
    payload: LibraryMemberIn,
    _: User = Depends(get_current_user),
    service: LibraryService = Depends(_library),
):
    return service.create_member(payload)


@router.get("/library/members/{member_id}", response_model=LibraryMemberOut)
def get_member(
    member_id: int, _: User = Depends(get_current_user), service: LibraryService = Depends(_library)
):
    return service.get_member(member_id)


@router.post("/library/loans", response_model=LoanOut, status_code=201)
def borrow_book(
    payload: LoanIn, _: User = Depends(get_current_user), service: LibraryService = Depends(_library)
):
    return service.borrow(payload)


@router.post("/library/loans/{loan_id}/return", response_model=LoanOut)
def return_book(
    loan_id: int, _: User = Depends(get_current_user), service: LibraryService = Depends(_library)
):
    return service.return_loan(loan_id)


@router.get("/library/members/{member_id}/loans", response_model=list[LoanOut])
def active_loans(
    member_id: int, _: User = Depends(get_current_user), service: LibraryService = Depends(_library)
):
    return service.active_loans(member_id)


@router.post("/library/reservations", response_model=ReservationOut, status_code=201)
def reserve_book(
    payload: ReservationIn,
    _: User = Depends(get_current_user),
    service: LibraryService = Depends(_library),
):
    return service.reserve(payload)


@router.get("/library/reservations", response_model=list[ReservationOut])
def list_reservations(
    member_id: int | None = None,
    _: User = Depends(get_current_user),
    service: LibraryService = Depends(_library),
):
    return service.list_reservations(member_id)
