# Data ownership — SEMS-R six-service reconstruction

This is the **historical/reference materialization** of SEMS-R, not original SEMS, and not a scored decomposition prediction. Services do not import each other's ORM models.

## Ownership

| Service | Owns | Reaches others via |
| --- | --- | --- |
| Gateway / identity | `User` (passwords, JWT) | Proxies public `/api/v1` routes |
| Faculty | Faculty, Department, Staff, Teacher, Course, AcademicYear, Semester | Identity (create staff users) |
| Student | Student, SemesterRegistration, CourseEnrollment | Identity, Faculty (course/semester), Finance (holds, account create) |
| Grade | Exam, ExamRegistration, Grade, GradeHistory | Student (enrollment), Faculty (course/teacher). Local `course_projections` |
| Finance | StudentAccount, Fee, Invoice, Payment, transactions, faculty ledger | Student (faculty_id projection), Faculty (optional verify) |
| Attendance | ClassSession, StudentAttendance, StaffAttendance | Faculty (course/teacher/staff), Student (enrollment) |
| Library | Book, BookCopy, LibraryMember, Loan, Reservation | Identity, Student (active status), Faculty (staff membership) |

## Difficult cases

**User.** Gateway-owned shared identity. Services store `user_id` integers only. JWT secret is shared (reconstruction choice, not a production IAM design).

**CourseEnrollment.** Owned by Student. Grade and Attendance ask Student `GET /internal/enrollments` rather than replicating enrollment rows.

**Student overview / faculty statistics.** BFF-style aggregation over HTTP. ReportBuilder's cross-table SQL is replaced by peer calls; it is not reintroduced as a shared database.

**IDs.** Owning service assigns primary keys. Other services store those IDs without foreign keys across databases.

## What this is not

- Not a service mesh, saga, or event bus.
- Not Mode B scaling. Mode A comparison is `make compare-load` (`experiments/configs/mode_a.yaml`).
- Not an LLM-generated architecture. Optional method-specific materialization is out of scope until a decomposition is chosen explicitly.
- Mode E (`clustered` profile) is a **runtime** split: campus process + library HTTP. It is not this six-service gold and is not scored as a decomposition.
