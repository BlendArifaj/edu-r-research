from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

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
from common.auth import require_user
from common.peers import get_peers
from finance.deps import get_db
from finance.service import FinanceService

router = APIRouter()
internal = APIRouter(prefix="/internal")


class AccountEnsureIn(BaseModel):
    faculty_id: int | None = None


def _service(db: Session = Depends(get_db)) -> FinanceService:
    return FinanceService(db, get_peers())


@router.get("/api/v1/students/{student_id}/account", response_model=AccountOut)
def get_account(
    student_id: int, _: dict = Depends(require_user), service: FinanceService = Depends(_service)
):
    return service.get_account(student_id)


@router.post("/api/v1/fees", response_model=FeeOut, status_code=201)
def create_fee(payload: FeeIn, _: dict = Depends(require_user), service: FinanceService = Depends(_service)):
    return service.create_fee(payload)


@router.get("/api/v1/fees", response_model=list[FeeOut])
def list_fees(_: dict = Depends(require_user), service: FinanceService = Depends(_service)):
    return service.list_fees()


@router.post("/api/v1/invoices", response_model=InvoiceOut, status_code=201)
def create_invoice(
    payload: InvoiceIn, _: dict = Depends(require_user), service: FinanceService = Depends(_service)
):
    return service.create_invoice(payload)


@router.get("/api/v1/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int, _: dict = Depends(require_user), service: FinanceService = Depends(_service)
):
    return service.get_invoice(invoice_id)


@router.get("/api/v1/students/{student_id}/invoices", response_model=list[InvoiceOut])
def list_invoices(
    student_id: int, _: dict = Depends(require_user), service: FinanceService = Depends(_service)
):
    return service.list_student_invoices(student_id)


@router.post("/api/v1/payments", response_model=PaymentOut, status_code=201)
def record_payment(
    payload: PaymentIn, _: dict = Depends(require_user), service: FinanceService = Depends(_service)
):
    return service.record_payment(payload)


@router.get("/api/v1/students/{student_id}/transactions", response_model=list[TransactionOut])
def list_transactions(
    student_id: int, _: dict = Depends(require_user), service: FinanceService = Depends(_service)
):
    return service.list_transactions(student_id)


@router.get("/api/v1/faculties/{faculty_id}/finance-summary", response_model=FacultyFinanceOut)
def faculty_finance(
    faculty_id: int, _: dict = Depends(require_user), service: FinanceService = Depends(_service)
):
    summary = service.faculty_summary(faculty_id, verify=True)
    return FacultyFinanceOut(
        faculty_id=faculty_id,
        collected_fees=summary["collected_fees"],
        ledger_net=summary["ledger_net"],
    )


@internal.get("/holds/{student_id}")
def internal_holds(
    student_id: int, _: dict = Depends(require_user), service: FinanceService = Depends(_service)
):
    return {"outstanding": service.has_outstanding_balance(student_id)}


@internal.post("/accounts/{student_id}")
def internal_ensure_account(
    student_id: int,
    payload: AccountEnsureIn | None = None,
    _: dict = Depends(require_user),
    service: FinanceService = Depends(_service),
):
    faculty_id = payload.faculty_id if payload else None
    account = service.ensure_account(student_id, faculty_id=faculty_id)
    return {"id": account.id, "student_id": account.student_id, "balance": str(account.balance)}


@internal.get("/faculty-summary/{faculty_id}")
def internal_faculty_summary(
    faculty_id: int, _: dict = Depends(require_user), service: FinanceService = Depends(_service)
):
    return service.faculty_summary(faculty_id)
