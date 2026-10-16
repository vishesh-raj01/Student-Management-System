"""SQLite persistence layer.

The repository knows nothing about the terminal. It raises typed exceptions
that the UI layer turns into friendly messages.
"""

import sqlite3
from contextlib import contextmanager

from models import Student
from validators import (
    MAX_GPA,
    MAX_SEMESTER,
    MIN_SEMESTER,
    ValidationError,
    normalize_roll_no,
    validate_fields,
)


class StorageError(Exception):
    """Base class for storage problems."""


class DuplicateRollNumberError(StorageError):
    """A student with this roll number already exists."""


class StudentNotFoundError(StorageError):
    """No student matches the requested roll number."""


_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS students (
    roll_no    TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL,
    department TEXT NOT NULL,
    semester   INTEGER NOT NULL CHECK (semester BETWEEN {MIN_SEMESTER} AND {MAX_SEMESTER}),
    gpa        REAL NOT NULL CHECK (gpa >= 0 AND gpa <= {MAX_GPA})
)
"""

_UPDATABLE = {"name", "email", "department", "semester", "gpa"}


class StudentRepository:
    def __init__(self, db_path: str = "students.db"):
        self.db_path = db_path
        with self._connect() as conn:
            conn.execute(_SCHEMA)

    @contextmanager
    def _connect(self):
        """Open a connection, commit on success, roll back on error, always close."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
        except sqlite3.Error as exc:
            raise StorageError(f"Cannot open database '{self.db_path}': {exc}") from exc
        try:
            with conn:
                yield conn
        except sqlite3.Error as exc:
            raise StorageError(f"Database error: {exc}") from exc
        finally:
            conn.close()

    @staticmethod
    def _row_to_student(row: sqlite3.Row) -> Student:
        return Student(**dict(row))

    # ---- Create -------------------------------------------------------
    def add(self, student: Student) -> None:
        with self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO students (roll_no, name, email, department, semester, gpa) "
                    "VALUES (:roll_no, :name, :email, :department, :semester, :gpa)",
                    student.to_dict(),
                )
            except sqlite3.IntegrityError as exc:
                if "UNIQUE" in str(exc) or "PRIMARY KEY" in str(exc):
                    raise DuplicateRollNumberError(
                        f"Roll number {student.roll_no} already exists."
                    ) from exc
                raise

    # ---- Read ---------------------------------------------------------
    def exists(self, roll_no: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM students WHERE roll_no = ?", (normalize_roll_no(roll_no),)
            ).fetchone()
        return row is not None

    def get(self, roll_no: str) -> Student:
        roll = normalize_roll_no(roll_no)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM students WHERE roll_no = ?", (roll,)
            ).fetchone()
        if row is None:
            raise StudentNotFoundError(f"No student with roll number {roll}.")
        return self._row_to_student(row)

    def list_all(self) -> list:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM students ORDER BY roll_no").fetchall()
        return [self._row_to_student(r) for r in rows]

    def search(self, query: str) -> list:
        """Case-insensitive partial match on roll number or name."""
        q = query.strip().casefold()
        if not q:
            raise ValidationError("Search text cannot be empty.")
        return [
            s
            for s in self.list_all()
            if q in s.roll_no.casefold() or q in s.name.casefold()
        ]

    # ---- Update -------------------------------------------------------
    def update(self, roll_no: str, /, **changes) -> Student:
        if not changes:
            raise ValidationError("Nothing to update.")
        bad = set(changes) - _UPDATABLE
        if bad:
            raise ValidationError(f"Cannot update field(s): {', '.join(sorted(bad))}")
        current = self.get(roll_no)  # raises StudentNotFoundError
        cleaned = validate_fields(**changes)
        assignments = ", ".join(f"{col} = :{col}" for col in cleaned)
        with self._connect() as conn:
            conn.execute(
                f"UPDATE students SET {assignments} WHERE roll_no = :roll_no",
                {**cleaned, "roll_no": current.roll_no},
            )
        return self.get(current.roll_no)

    # ---- Delete -------------------------------------------------------
    def delete(self, roll_no: str) -> None:
        roll = normalize_roll_no(roll_no)
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM students WHERE roll_no = ?", (roll,))
            if cur.rowcount == 0:
                raise StudentNotFoundError(f"No student with roll number {roll}.")
