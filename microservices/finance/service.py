from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, DomainError
from app.schemas import FeeIn, InvoiceIn, PaymentIn
from common.http import Peers
from finance.models import (
    FacultyLedgerEntry,
    Fee,
    FinancialTransaction,
    Invoice,
    InvoiceLine,
    Payment,
    StudentAccount,
    StudentProjection,
    account_for_student,
    collected_fees,
    faculty_net,
    require_account,
    require_fee,
    require_invoice,
)


class FinanceService:
    def __init__(self, db: Session, peers: Peers) -> None:
        self.db = db
        self.peers = peers

    def ensure_account(self, student_id: int, faculty_id: int | None = None) -> StudentAccount:
        if faculty_id is not None:
            self.db.merge(StudentProjection(id=student_id, faculty_id=faculty_id))
            self.db.flush()
        else:
            self._student(student_id)
        account = account_for_student(self.db, student_id)
        if account is None:
            account = StudentAccount(student_id=student_id, balance=Decimal("0.00"))
            self.db.add(account)
            self.db.flush()
        return account

    def get_account(self, student_id: int) -> StudentAccount:
        return self.ensure_account(student_id)

    def has_outstanding_balance(self, student_id: int) -> bool:
        return self.ensure_account(student_id).balance > Decimal("0.00")

    def create_fee(self, data: FeeIn) -> Fee:
        if data.faculty_id is not None:
            self.peers.call("faculty", "GET", f"/internal/faculties/{data.faculty_id}")
        fee = Fee(**data.model_dump())
        self.db.add(fee)
        self.db.flush()
        return fee

    def list_fees(self) -> list[Fee]:
        return list(self.db.scalars(select(Fee)))

    def create_invoice(self, data: InvoiceIn) -> Invoice:
        student = self._student(data.student_id)
        self.peers.call("faculty", "GET", f"/internal/semesters/{data.semester_id}")
        account = self.ensure_account(student["id"])
        fees = [require_fee(self.db, fee_id) for fee_id in data.fee_ids]
        total = sum((fee.amount for fee in fees), Decimal("0.00"))
        invoice = Invoice(
            student_account_id=account.id,
            semester_id=data.semester_id,
            total=total,
            status="open",
            issued_at=datetime.now(UTC),
        )
        invoice.lines = [
            InvoiceLine(fee_id=fee.id, amount=fee.amount, description=fee.name) for fee in fees
        ]
        self.db.add(invoice)
        self.db.flush()
        account.balance += total
        self.db.add(
            FinancialTransaction(
                student_account_id=account.id,
                amount=total,
                txn_type="charge",
                reference=f"invoice:{invoice.id}",
                created_at_txn=datetime.now(UTC),
            )
        )
        self.db.flush()
        return invoice

    def get_invoice(self, invoice_id: int) -> Invoice:
        return require_invoice(self.db, invoice_id)

    def list_student_invoices(self, student_id: int) -> list[Invoice]:
        account = self.ensure_account(student_id)
        return list(self.db.scalars(select(Invoice).where(Invoice.student_account_id == account.id)))

    def record_payment(self, data: PaymentIn) -> Payment:
        invoice = require_invoice(self.db, data.invoice_id)
        if invoice.status == "void":
            raise DomainError("cannot pay a void invoice")
        account = require_account(self.db, invoice.student_account_id)
        paid = sum((p.amount for p in invoice.payments), Decimal("0.00"))
        if paid + data.amount > invoice.total:
            raise ConflictError("payment exceeds invoice total")
        payment = Payment(
            invoice_id=invoice.id,
            student_account_id=account.id,
            amount=data.amount,
            method=data.method,
            paid_at=datetime.now(UTC),
        )
        self.db.add(payment)
        self.db.flush()
        account.balance -= data.amount
        new_paid = paid + data.amount
        invoice.status = "paid" if new_paid == invoice.total else "partial"
        self.db.add(
            FinancialTransaction(
                student_account_id=account.id,
                amount=data.amount,
                txn_type="payment",
                reference=f"payment:{payment.id}",
                created_at_txn=datetime.now(UTC),
            )
        )
        student = self._student(account.student_id)
        self.db.add(
            FacultyLedgerEntry(
                faculty_id=int(student["faculty_id"]),
                entry_type="income",
                amount=data.amount,
                description=f"payment {payment.id}",
                occurred_at=datetime.now(UTC),
            )
        )
        self.db.flush()
        return payment

    def list_transactions(self, student_id: int):
        account = self.ensure_account(student_id)
        return list(
            self.db.scalars(
                select(FinancialTransaction).where(
                    FinancialTransaction.student_account_id == account.id
                )
            )
        )

    def faculty_summary(self, faculty_id: int, *, verify: bool = False) -> dict[str, str]:
        if verify:
            self.peers.call("faculty", "GET", f"/internal/faculties/{faculty_id}")
        return {
            "faculty_id": faculty_id,
            "collected_fees": str(collected_fees(self.db, faculty_id)),
            "ledger_net": str(faculty_net(self.db, faculty_id)),
        }

    def _student(self, student_id: int) -> dict:
        projection = self.db.get(StudentProjection, student_id)
        if projection is None:
            payload = self.peers.call("student", "GET", f"/internal/students/{student_id}")
            projection = StudentProjection(id=int(payload["id"]), faculty_id=int(payload["faculty_id"]))
            self.db.merge(projection)
            self.db.flush()
            return payload
        return {"id": projection.id, "faculty_id": projection.faculty_id}
