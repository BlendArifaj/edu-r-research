from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import (
    FacultyLedgerEntry,
    Fee,
    FinancialTransaction,
    Invoice,
    Payment,
    StudentAccount,
)


class FinanceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_account(self, account_id: int) -> StudentAccount:
        account = self.db.get(StudentAccount, account_id)
        if account is None:
            raise NotFoundError("StudentAccount", account_id)
        return account

    def get_account_for_student(self, student_id: int) -> StudentAccount | None:
        return self.db.scalar(select(StudentAccount).where(StudentAccount.student_id == student_id))

    def add_account(self, account: StudentAccount) -> StudentAccount:
        self.db.add(account)
        self.db.flush()
        return account

    def get_invoice(self, invoice_id: int) -> Invoice:
        invoice = self.db.get(Invoice, invoice_id)
        if invoice is None:
            raise NotFoundError("Invoice", invoice_id)
        return invoice

    def list_invoices_for_account(self, account_id: int) -> list[Invoice]:
        stmt = select(Invoice).where(Invoice.student_account_id == account_id).order_by(Invoice.id)
        return list(self.db.scalars(stmt).all())

    def add_invoice(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        self.db.flush()
        return invoice

    def add_fee(self, fee: Fee) -> Fee:
        self.db.add(fee)
        self.db.flush()
        return fee

    def list_fees(self) -> list[Fee]:
        return list(self.db.scalars(select(Fee).order_by(Fee.id)).all())

    def get_fee(self, fee_id: int) -> Fee:
        fee = self.db.get(Fee, fee_id)
        if fee is None:
            raise NotFoundError("Fee", fee_id)
        return fee

    def add_payment(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.flush()
        return payment

    def add_transaction(self, txn: FinancialTransaction) -> FinancialTransaction:
        self.db.add(txn)
        self.db.flush()
        return txn

    def list_transactions(self, account_id: int) -> list[FinancialTransaction]:
        stmt = (
            select(FinancialTransaction)
            .where(FinancialTransaction.student_account_id == account_id)
            .order_by(FinancialTransaction.id)
        )
        return list(self.db.scalars(stmt).all())

    def open_balance_for_student(self, student_id: int) -> Decimal:
        account = self.get_account_for_student(student_id)
        if account is None:
            return Decimal("0.00")
        return account.balance

    def add_ledger_entry(self, entry: FacultyLedgerEntry) -> FacultyLedgerEntry:
        self.db.add(entry)
        self.db.flush()
        return entry

    def faculty_net(self, faculty_id: int) -> Decimal:
        income = self.db.scalar(
            select(func.coalesce(func.sum(FacultyLedgerEntry.amount), 0)).where(
                FacultyLedgerEntry.faculty_id == faculty_id,
                FacultyLedgerEntry.entry_type == "income",
            )
        )
        expense = self.db.scalar(
            select(func.coalesce(func.sum(FacultyLedgerEntry.amount), 0)).where(
                FacultyLedgerEntry.faculty_id == faculty_id,
                FacultyLedgerEntry.entry_type == "expense",
            )
        )
        return (Decimal(str(income or 0)) - Decimal(str(expense or 0))).quantize(Decimal("0.01"))
