"""
Model
-----
CSV export/import for tasks. Pure I/O, no tkinter dependency. Called from
the "Task List" tab's export/import buttons, via the Presenter.

Exceptions propagate uncaught (OSError, UnicodeDecodeError, csv.Error,
ValueError); the Presenter catches them and reports via view.show_message().
"""

import csv
from typing import List, Tuple

from task_manager_tkinter.model.task.entity import STATUSES, Task

FIELDNAMES = ["name", "assignee", "due_date", "priority", "status"]


def export_tasks_to_csv(tasks: List[Task], path: str) -> None:
    """Write the task list out to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for t in tasks:
            writer.writerow(
                {
                    "name": t.name,
                    "assignee": t.assignee,
                    "due_date": t.due_date,
                    "priority": t.priority,
                    "status": t.status,
                }
            )


def import_tasks_from_csv(path: str) -> Tuple[List[Task], int]:
    """Read tasks from a CSV file. Returns (tasks, count skipped for blank name)."""
    tasks: List[Task] = []
    skipped = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if "name" not in (reader.fieldnames or []):
            # Not a CSV this app produced — raise rather than silently import 0 rows
            raise ValueError(
                "The CSV file has no 'name' column — "
                "import a CSV that was exported by this app."
            )
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                skipped += 1
                continue
            # Fold retired status values (e.g. old "Overdue") into "Not Started"
            status = row.get("status") or "Not Started"
            if status not in STATUSES:
                status = "Not Started"
            tasks.append(
                Task(
                    name=name,
                    assignee=row.get("assignee", ""),
                    due_date=row.get("due_date", ""),
                    priority=row.get("priority") or "Medium",
                    status=status,
                )
            )
    return tasks, skipped
