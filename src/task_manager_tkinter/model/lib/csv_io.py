"""
Model
-----
CSV export/import for tasks. Pure I/O logic with no dependency on tkinter.
Called from the "Task List" tab's export/import buttons, via the Presenter.

Exceptions are not swallowed here; they are simply passed on to the caller
(the Presenter). Possible exceptions are: OSError (file can't be opened,
permissions, disk, etc.), UnicodeDecodeError (invalid encoding; a subclass
of ValueError), csv.Error (malformed CSV), and ValueError (e.g. a required
column is missing — raised explicitly below). The Presenter catches these
and reports them to the user via view.show_message().
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
    """Read tasks in from a CSV file.

    Returns: (list of Tasks that were read, number of rows skipped because the task name was blank)
    """
    tasks: List[Task] = []
    skipped = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if "name" not in (reader.fieldnames or []):
            # No "name" column in the header — this isn't a CSV produced by
            # this app. Rather than skip every row and silently report
            # "0 imported", raise a clear error instead.
            raise ValueError(
                "The CSV file has no 'name' column — "
                "import a CSV that was exported by this app."
            )
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                skipped += 1
                continue
            # Fold status values that no longer exist (e.g. "Overdue", written
            # by an older version) into "Not Started" — "Overdue" is not a
            # status; it's derived from due_date instead.
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
