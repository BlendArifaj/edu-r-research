from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    AccountOut,
    FacultyFinanceOut,
    FeeIn,
    FeeOut,
    InvoiceIn,
    InvoiceOut,
    PaymentIn,
    PaymentOut,
    TransactionOut,
)
from app.services import FacultyStatisticsService, FinanceService

router = APIRouter(tags=["finance"])


def _finance(db: Session = Depends(get_db)) -> FinanceService:
    return FinanceService(db)


@router.get("/students/{student_id}/account", response_model=AccountOut)
def get_account(
    student_id: int, _: User = Depends(get_current_user), service: FinanceService = Depends(_finance)
):
    return service.get_account(student_id)


@router.post("/fees", response_model=FeeOut, status_code=201)
def create_fee(
    payload: FeeIn, _: User = Depends(get_current_user), service: FinanceService = Depends(_finance)
):
    return service.create_fee(payload)


@router.get("/fees", response_model=list[FeeOut])
def list_fees(_: User = Depends(get_current_user), service: FinanceService = Depends(_finance)):
    return service.list_fees()


@router.post("/invoices", response_model=InvoiceOut, status_code=201)
def create_invoice(
    payload: InvoiceIn, _: User = Depends(get_current_user), service: FinanceService = Depends(_finance)
):
    return service.create_invoice(payload)


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int, _: User = Depends(get_current_user), service: FinanceService = Depends(_finance)
):
    return service.get_invoice(invoice_id)


@router.get("/students/{student_id}/invoices", response_model=list[InvoiceOut])
def list_invoices(
    student_id: int, _: User = Depends(get_current_user), service: FinanceService = Depends(_finance)
):
    return service.list_student_invoices(student_id)


@router.post("/payments", response_model=PaymentOut, status_code=201)
def record_payment(
    payload: PaymentIn, _: User = Depends(get_current_user), service: FinanceService = Depends(_finance)
):
    return service.record_payment(payload)


@router.get("/students/{student_id}/transactions", response_model=list[TransactionOut])
def list_transactions(
    student_id: int, _: User = Depends(get_current_user), service: FinanceService = Depends(_finance)
):
    return service.list_transactions(student_id)


@router.get("/faculties/{faculty_id}/finance-summary", response_model=FacultyFinanceOut)
def faculty_finance(
    faculty_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return FacultyStatisticsService(db).finance_summary(faculty_id)
