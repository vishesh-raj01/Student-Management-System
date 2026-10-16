"""Create students.db pre-populated with sample records.

Usage: python seed.py [path/to/file.db]
Existing roll numbers are skipped, so it is safe to run more than once.
"""

import os
import sys

from models import Student
from storage import DuplicateRollNumberError, StudentRepository

SAMPLE = [
    ("ELX-001", "Aarav Sharma", "aarav.sharma@example.com", "Electronics", 5, 8.4),
    ("ELX-002", "Priya Verma", "priya.verma@example.com", "Electronics", 5, 9.1),
    ("ELX-003", "Rohan Gupta", "rohan.gupta@example.com", "Electronics", 3, 7.2),
    ("ELX-004", "Sneha Singh", "sneha.singh@example.com", "Electronics", 3, 8.8),
    ("CSE-001", "Mohammad Aman", "aman.m@example.com", "Computer Science", 5, 7.9),
    ("CSE-002", "Anjali Yadav", "anjali.yadav@example.com", "Computer Science", 1, 9.4),
    ("MEC-001", "Vikram Patel", "vikram.patel@example.com", "Mechanical", 5, 6.8),
    ("MEC-002", "Kavita Mishra", "kavita.mishra@example.com", "Mechanical", 3, 7.5),
    ("CIV-001", "Suresh Kumar", "suresh.kumar@example.com", "Civil", 1, 6.2),
    ("CIV-002", "Neha O'Connor", "neha.oconnor@example.com", "Civil", 5, 8.0),
]


def main():
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.db")
    path = sys.argv[1] if len(sys.argv) > 1 else default
    repo = StudentRepository(path)
    added = 0
    for row in SAMPLE:
        try:
            repo.add(Student.create(*row))
            added += 1
        except DuplicateRollNumberError:
            pass
    print(f"{added} sample record(s) added to {path}")


if __name__ == "__main__":
    main()
