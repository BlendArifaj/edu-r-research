from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.exceptions import ConflictError, DomainError
from app.models import (
    FacultyLedgerEntry,
    Fee,
    FinancialTransaction,
    Invoice,
    InvoiceLine,
    Payment,
    StudentAccount,
)
from app.models.enums import InvoiceStatus, TransactionType
from app.repositories import (
    AcademicCalendarRepository,
    FacultyRepository,
    FinanceRepository,
    StudentRepository,
)
from app.schemas import FeeIn, InvoiceIn, PaymentIn


class FinanceService:
    """Finance reads Student and Faculty records directly (shared-database coupling)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.finance = FinanceRepository(db)
        self.students = StudentRepository(db)
        self.faculties = FacultyRepository(db)
        self.calendar = AcademicCalendarRepository(db)

    def ensure_account(self, student_id: int) -> StudentAccount:
        student = self.students.get(student_id)
        account = self.finance.get_account_for_student(student.id)
        if account is None:
            account = self.finance.add_account(StudentAccount(student_id=student.id, balance=Decimal("0.00")))
        return account

    def get_account(self, student_id: int) -> StudentAccount:
        return self.ensure_account(student_id)

    def has_outstanding_balance(self, student_id: int) -> bool:
        return self.ensure_account(student_id).balance > Decimal("0.00")

    def create_fee(self, data: FeeIn) -> Fee:
        if data.faculty_id is not None:
            self.faculties.get(data.faculty_id)
        return self.finance.add_fee(Fee(**data.model_dump()))

    def list_fees(self):
        return self.finance.list_fees()

    def create_invoice(self, data: InvoiceIn) -> Invoice:
        student = self.students.get(data.student_id)
        self.calendar.get_semester(data.semester_id)
        account = self.ensure_account(student.id)
        fees = [self.finance.get_fee(fee_id) for fee_id in data.fee_ids]
        total = sum((fee.amount for fee in fees), Decimal("0.00"))
        invoice = Invoice(
            student_account_id=account.id,
            semester_id=data.semester_id,
            total=total,
            status=InvoiceStatus.OPEN,
            issued_at=datetime.now(UTC),
        )
        invoice.lines = [
            InvoiceLine(fee_id=fee.id, amount=fee.amount, description=fee.name) for fee in fees
        ]
        self.finance.add_invoice(invoice)
        account.balance += total
        self.finance.add_transaction(
            FinancialTransaction(
                student_account_id=account.id,
                amount=total,
                txn_type=TransactionType.CHARGE,
                reference=f"invoice:{invoice.id}",
                created_at_txn=datetime.now(UTC),
            )
        )
        self.db.flush()
        return invoice

    def get_invoice(self, invoice_id: int) -> Invoice:
        return self.finance.get_invoice(invoice_id)

    def list_student_invoices(self, student_id: int) -> list[Invoice]:
        account = self.ensure_account(student_id)
        return self.finance.list_invoices_for_account(account.id)

    def record_payment(self, data: PaymentIn) -> Payment:
        invoice = self.finance.get_invoice(data.invoice_id)
        if invoice.status == InvoiceStatus.VOID:
            raise DomainError("cannot pay a void invoice")
        account = self.finance.get_account(invoice.student_account_id)
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
        self.finance.add_payment(payment)
        account.balance -= data.amount
        new_paid = paid + data.amount
        invoice.status = InvoiceStatus.PAID if new_paid == invoice.total else InvoiceStatus.PARTIAL
        self.finance.add_transaction(
            FinancialTransaction(
                student_account_id=account.id,
                amount=data.amount,
                txn_type=TransactionType.PAYMENT,
                reference=f"payment:{payment.id}",
                created_at_txn=datetime.now(UTC),
            )
        )
        student = self.students.get(account.student_id)
        self.finance.add_ledger_entry(
            FacultyLedgerEntry(
                faculty_id=student.faculty_id,
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
        return self.finance.list_transactions(account.id)
