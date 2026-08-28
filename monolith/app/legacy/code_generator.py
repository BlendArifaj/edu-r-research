"""Legacy code-generation helpers shared across faculty, student, and library."""


def faculty_code(name: str, sequence: int) -> str:
    prefix = "".join(part[0] for part in name.split() if part).upper()[:4] or "FAC"
    return f"{prefix}-{sequence:03d}"


def student_number(year: int, sequence: int) -> str:
    return f"{year}{sequence:05d}"


def staff_number(faculty_code_value: str, sequence: int) -> str:
    return f"STF-{faculty_code_value}-{sequence:04d}"


def member_number(member_type: str, sequence: int) -> str:
    prefix = "STU" if member_type == "student" else "STF"
    return f"LIB-{prefix}-{sequence:05d}"
