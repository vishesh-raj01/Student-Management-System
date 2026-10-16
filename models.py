"""Student data model."""

from dataclasses import asdict, dataclass

from validators import validate_fields


@dataclass
class Student:
    roll_no: str
    name: str
    email: str
    department: str
    semester: int
    gpa: float

    @classmethod
    def create(cls, roll_no, name, email, department, semester, gpa) -> "Student":
        """Build a Student from raw input, validating every field."""
        cleaned = validate_fields(
            roll_no=roll_no,
            name=name,
            email=email,
            department=department,
            semester=semester,
            gpa=gpa,
        )
        return cls(**cleaned)

    def to_dict(self) -> dict:
        return asdict(self)
