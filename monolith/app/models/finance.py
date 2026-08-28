from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin
from app.models.enums import InvoiceStatus, LedgerEntryType, PaymentMethod, TransactionType


class StudentAccount(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "student_accounts"

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"), unique=True, nullable=False, index=True
    )
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    student: Mapped["Student"] = relationship(back_populates="account")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="account")
    payments: Mapped[list["Payment"]] = relationship(back_populates="account")
    transactions: Mapped[list["FinancialTransaction"]] = relationship(back_populates="account")


class Fee(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fees"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fee_type: Mapped[str] = mapped_column(String(32), nullable=False)
    academic_year_id: Mapped[int | None] = mapped_column(
        ForeignKey("academic_years.id"), nullable=True
    )
    faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculties.id"), nullable=True)


class Invoice(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "invoices"

    student_account_id: Mapped[int] = mapped_column(
        ForeignKey("student_accounts.id"), nullable=False, index=True
    )
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False, index=True)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=InvoiceStatus.OPEN, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    account: Mapped[StudentAccount] = relationship(back_populates="invoices")
    lines: Mapped[list["InvoiceLine"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(back_populates="invoice")


class InvoiceLine(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "invoice_lines"

    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    fee_id: Mapped[int] = mapped_column(ForeignKey("fees.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    invoice: Mapped[Invoice] = relationship(back_populates="lines")
    fee: Mapped[Fee] = relationship()


class Payment(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    student_account_id: Mapped[int] = mapped_column(
        ForeignKey("student_accounts.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(32), default=PaymentMethod.BANK, nullable=False)
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
    """Faculty income/expense rows written by finance while reading Faculty records."""

    __tablename__ = "faculty_ledger_entries"

    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"), nullable=False, index=True)
    entry_type: Mapped[str] = mapped_column(
        String(32), default=LedgerEntryType.INCOME, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
