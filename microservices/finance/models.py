from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.exceptions import NotFoundError
from common.models import PrimaryKeyMixin, TimestampMixin, make_base

Base = make_base()


class StudentProjection(TimestampMixin, Base):
    __tablename__ = "student_projections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    faculty_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)


class StudentAccount(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "student_accounts"

    student_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    invoices: Mapped[list["Invoice"]] = relationship(back_populates="account")
    payments: Mapped[list["Payment"]] = relationship(back_populates="account")
    transactions: Mapped[list["FinancialTransaction"]] = relationship(back_populates="account")


class Fee(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fees"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fee_type: Mapped[str] = mapped_column(String(32), nullable=False)
    academic_year_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    faculty_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Invoice(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "invoices"

    student_account_id: Mapped[int] = mapped_column(
        ForeignKey("student_accounts.id"), nullable=False, index=True
    )
    semester_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    account: Mapped[StudentAccount] = relationship(back_populates="invoices")
    lines: Mapped[list["InvoiceLine"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(back_populates="invoice")


class InvoiceLine(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "invoice_lines"

    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    fee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    invoice: Mapped[Invoice] = relationship(back_populates="lines")


class Payment(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    student_account_id: Mapped[int] = mapped_column(
        ForeignKey("student_accounts.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(32), default="bank", nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    invoice: Mapped[Invoice] = relationship(back_populates="payments")
    account: Mapped[StudentAccount] = relationship(back_populates="payments")


class FinancialTransaction(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "financial_transactions"

    student_account_id: Mapped[int] = mapped_column(
        ForeignKey("student_accounts.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    txn_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reference: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at_txn: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    account: Mapped[StudentAccount] = relationship(back_populates="transactions")


class FacultyLedgerEntry(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "faculty_ledger_entries"

    faculty_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    entry_type: Mapped[str] = mapped_column(String(32), default="income", nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def require_account(db: Session, account_id: int) -> StudentAccount:
    row = db.get(StudentAccount, account_id)
    if row is None:
        raise NotFoundError("StudentAccount", account_id)
    return row


def account_for_student(db: Session, student_id: int) -> StudentAccount | None:
    return db.scalar(select(StudentAccount).where(StudentAccount.student_id == student_id))


def require_invoice(db: Session, invoice_id: int) -> Invoice:
    row = db.get(Invoice, invoice_id)
    if row is None:
        raise NotFoundError("Invoice", invoice_id)
    return row


def require_fee(db: Session, fee_id: int) -> Fee:
    row = db.get(Fee, fee_id)
    if row is None:
        raise NotFoundError("Fee", fee_id)
    return row


def faculty_net(db: Session, faculty_id: int) -> Decimal:
    income = db.scalar(
        select(func.coalesce(func.sum(FacultyLedgerEntry.amount), 0)).where(
            FacultyLedgerEntry.faculty_id == faculty_id,
            FacultyLedgerEntry.entry_type == "income",
        )
    )
    expense = db.scalar(
        select(func.coalesce(func.sum(FacultyLedgerEntry.amount), 0)).where(
            FacultyLedgerEntry.faculty_id == faculty_id,
            FacultyLedgerEntry.entry_type == "expense",
        )
    )
    return Decimal(str(income or 0)) - Decimal(str(expense or 0))


def collected_fees(db: Session, faculty_id: int) -> Decimal:
    value = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .join(StudentAccount, StudentAccount.id == Payment.student_account_id)
        .join(StudentProjection, StudentProjection.id == StudentAccount.student_id)
        .where(StudentProjection.faculty_id == faculty_id)
    )
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))
