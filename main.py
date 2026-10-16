import argparse
import os
import sys

from models import Student
from storage import (
    DuplicateRollNumberError,
    StorageError,
    StudentNotFoundError,
    StudentRepository,
)
from validators import (
    ValidationError,
    validate_department,
    validate_email,
    validate_gpa,
    validate_name,
    validate_roll_no,
    validate_semester,
)

DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.db")

MENU = """
==============================
 Student Record Management
==============================
 1. Add student
 2. View all students
 3. Search (roll no. or name)
 4. Update student
 5. Delete student
 0. Exit
------------------------------"""


def ask(prompt, validator, current=None):
    """Prompt until the input validates. If `current` is given, Enter keeps it."""
    suffix = f" [{current}]" if current is not None else ""
    while True:
        raw = input(f"{prompt}{suffix}: ")
        if current is not None and not raw.strip():
            return current
        try:
            return validator(raw)
        except ValidationError as exc:
            print(f"  x {exc}")


def print_table(students):
    if not students:
        print("No records found.")
        return
    header = f"{'Roll No':<12}{'Name':<24}{'Email':<30}{'Dept':<18}{'Sem':<5}{'GPA':<5}"
    print(header)
    print("-" * len(header))
    for s in students:
        print(
            f"{s.roll_no:<12}{s.name[:22]:<24}{s.email[:28]:<30}"
            f"{s.department[:16]:<18}{s.semester:<5}{s.gpa:<5.2f}"
        )
    print(f"\n{len(students)} record(s).")


def add_student(repo):
    print("\n-- Add student (Ctrl+C to cancel) --")
    while True:
        roll = ask("Roll number", validate_roll_no)
        if repo.exists(roll):
            print(f"  x Roll number {roll} already exists. Choose another.")
            continue
        break
    student = Student.create(
        roll_no=roll,
        name=ask("Full name", validate_name),
        email=ask("Email", validate_email),
        department=ask("Department", validate_department),
        semester=ask("Semester (1-8)", validate_semester),
        gpa=ask("GPA", validate_gpa),
    )
    repo.add(student)
    print(f"Added {student.name} ({student.roll_no}).")


def view_all(repo):
    print()
    print_table(repo.list_all())


def search_students(repo):
    query = input("\nSearch text (roll no. or part of a name): ")
    print()
    print_table(repo.search(query))


def update_student(repo):
    print("\n-- Update student (Ctrl+C to cancel) --")
    roll = ask("Roll number to update", validate_roll_no)
    current = repo.get(roll)
    print_table([current])
    print("Press Enter to keep the current value.")
    changes = {
        "name": ask("Full name", validate_name, current.name),
        "email": ask("Email", validate_email, current.email),
        "department": ask("Department", validate_department, current.department),
        "semester": ask("Semester (1-8)", validate_semester, current.semester),
        "gpa": ask("GPA", validate_gpa, current.gpa),
    }
    changes = {k: v for k, v in changes.items() if getattr(current, k) != v}
    if not changes:
        print("No changes made.")
        return
    updated = repo.update(current.roll_no, **changes)
    print("Updated:")
    print_table([updated])


def delete_student(repo):
    print("\n-- Delete student (Ctrl+C to cancel) --")
    roll = ask("Roll number to delete", validate_roll_no)
    student = repo.get(roll)
    print_table([student])
    if input("Type 'yes' to confirm deletion: ").strip().lower() == "yes":
        repo.delete(student.roll_no)
        print("Record deleted.")
    else:
        print("Deletion cancelled.")


ACTIONS = {
    "1": add_student,
    "2": view_all,
    "3": search_students,
    "4": update_student,
    "5": delete_student,
}


def run(repo):
    while True:
        print(MENU)
        try:
            choice = input("Choose an option: ").strip()
            if choice == "0":
                print("Goodbye!")
                return
            action = ACTIONS.get(choice)
            if action is None:
                print("Invalid option. Please enter a number from the menu.")
                continue
            action(repo)
        except KeyboardInterrupt:
            print("\nCancelled. Returning to menu.")
        except EOFError:
            print("\nInput closed. Goodbye!")
            return
        except (DuplicateRollNumberError, StudentNotFoundError, ValidationError) as exc:
            print(f"Error: {exc}")
        except StorageError as exc:
            print(f"Storage problem: {exc}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Student Record Management System")
    parser.add_argument("--db", default=DEFAULT_DB, help="path to the SQLite file")
    args = parser.parse_args(argv)
    try:
        repo = StudentRepository(args.db)
    except StorageError as exc:
        print(f"Fatal: {exc}")
        return 1
    run(repo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
