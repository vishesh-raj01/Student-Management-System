"""Input validation helpers.

Every function takes raw user input and returns a cleaned value, or raises
ValidationError with a human-readable message. No function in this module
touches the database or the terminal.
"""

import math
import re

# Change MAX_GPA to 4.0 if your institution uses a 4-point scale.
MAX_GPA = 10.0
MIN_SEMESTER = 1
MAX_SEMESTER = 8

_ROLL_RE = re.compile(r"^[A-Z0-9][A-Z0-9_\-/]{1,19}$")
_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$"
)


class ValidationError(ValueError):
    """Raised when user input fails validation."""


def normalize_roll_no(value) -> str:
    """Trim and upper-case a roll number (used for lookups too)."""
    return str(value).strip().upper()


def validate_roll_no(value) -> str:
    roll = normalize_roll_no(value)
    if not roll:
        raise ValidationError("Roll number cannot be empty.")
    if not _ROLL_RE.match(roll):
        raise ValidationError(
            "Roll number must be 2-20 characters: letters, digits, '-', '_' or '/'."
        )
    return roll


def validate_name(value) -> str:
    name = " ".join(str(value).split())  # collapse extra whitespace
    if len(name) < 2 or len(name) > 60:
        raise ValidationError("Name must be between 2 and 60 characters.")
    if not all(ch.isalpha() or ch in " .'-" for ch in name):
        raise ValidationError(
            "Name may contain only letters, spaces, '.', '-' and apostrophes."
        )
    return name


def validate_email(value) -> str:
    email = str(value).strip()
    if not email:
        raise ValidationError("Email cannot be empty.")
    if len(email) > 100 or not _EMAIL_RE.match(email):
        raise ValidationError("Enter a valid email address (e.g. name@example.com).")
    return email.lower()


def validate_department(value) -> str:
    dept = " ".join(str(value).split())
    if len(dept) < 2 or len(dept) > 50:
        raise ValidationError("Department must be between 2 and 50 characters.")
    return dept


def validate_semester(value) -> int:
    text = str(value).strip()
    try:
        sem = int(text)
    except ValueError:
        raise ValidationError("Semester must be a whole number.") from None
    if not MIN_SEMESTER <= sem <= MAX_SEMESTER:
        raise ValidationError(
            f"Semester must be between {MIN_SEMESTER} and {MAX_SEMESTER}."
        )
    return sem


def validate_gpa(value) -> float:
    if isinstance(value, bool):
        raise ValidationError("GPA must be a number.")
    try:
        gpa = float(str(value).strip())
    except ValueError:
        raise ValidationError("GPA must be a number (e.g. 8.5).") from None
    if not math.isfinite(gpa):
        raise ValidationError("GPA must be a finite number.")
    if not 0.0 <= gpa <= MAX_GPA:
        raise ValidationError(f"GPA must be between 0.0 and {MAX_GPA}.")
    return round(gpa, 2)


# Field name -> validator, used for whole-record and partial (update) checks.
FIELD_VALIDATORS = {
    "roll_no": validate_roll_no,
    "name": validate_name,
    "email": validate_email,
    "department": validate_department,
    "semester": validate_semester,
    "gpa": validate_gpa,
}


def validate_fields(**fields) -> dict:
    """Validate any subset of student fields; unknown field names are rejected."""
    cleaned = {}
    for key, value in fields.items():
        if key not in FIELD_VALIDATORS:
            raise ValidationError(f"Unknown field: {key}")
        cleaned[key] = FIELD_VALIDATORS[key](value)
    return cleaned
