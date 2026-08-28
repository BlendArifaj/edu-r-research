from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    FACULTY_ADMIN = "faculty_admin"
    TEACHER = "teacher"
    STUDENT = "student"
    STAFF = "staff"
    LIBRARIAN = "librarian"
    FINANCE_OFFICER = "finance_officer"


class StudentStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    GRADUATED = "graduated"


class EmploymentType(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"


class EnrollmentStatus(StrEnum):
    ENROLLED = "enrolled"
    DROPPED = "dropped"
    COMPLETED = "completed"


class RegistrationStatus(StrEnum):
    REGISTERED = "registered"
    WITHDRAWN = "withdrawn"


class ExamType(StrEnum):
    MIDTERM = "midterm"
    FINAL = "final"
    MAKEUP = "makeup"


class InvoiceStatus(StrEnum):
    OPEN = "open"
    PAID = "paid"
    PARTIAL = "partial"
    VOID = "void"


class PaymentMethod(StrEnum):
    CASH = "cash"
    BANK = "bank"
    CARD = "card"


class TransactionType(StrEnum):
    CHARGE = "charge"
    PAYMENT = "payment"
    ADJUSTMENT = "adjustment"


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class CopyStatus(StrEnum):
    AVAILABLE = "available"
    ON_LOAN = "on_loan"
    RESERVED = "reserved"
    LOST = "lost"


class MemberType(StrEnum):
    STUDENT = "student"
    STAFF = "staff"


class LoanStatus(StrEnum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"


class ReservationStatus(StrEnum):
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class LedgerEntryType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
