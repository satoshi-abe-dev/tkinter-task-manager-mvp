"""
Model
-----
Holds only the domain logic for keeping, adding, updating, and deleting
tasks. Knows nothing about the View or the Presenter.

Edit operations (add/update/delete) only modify the in-memory _tasks; they
don't write to the DB on the spot. Changes are actually flushed to SQLite
only when save() is called explicitly (when the "Save" button on the list
tab is pressed). This means that if you make a mistake before saving, as
long as you don't save, restarting the app puts you right back to the last
saved state (restarting the app acts as an "undo everything").
"""

import re
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, List, Optional

from task_manager_tkinter.model.lib import task_db
from task_manager_tkinter.model.lib.db_path import DEFAULT_DB_PATH
from task_manager_tkinter.model.task.entity import Task

# Fields that inline editing on the list tab is allowed to change
EDITABLE_FIELDS = {"name", "assignee", "due_date", "priority", "status"}

# Pattern (full match) for picking out the "+ Add" placeholder task name "Task <number>"
_DEFAULT_TASK_NAME_RE = re.compile(r"Task ([0-9]+)")


def _next_default_task_name(existing_names: Iterable[str]) -> str:
    """The placeholder task name used by "+ Add": the highest existing
    "Task <number>" value + 1. "Task 1" if there are none.

    Numbering is based on the existing names, not the count or an id:
      - With only the seed data (no "Task N" present), it always starts at "Task 1"
      - Even if the user has typed in "Task 40" by hand or imported it via
        CSV, the next one will be "Task 41", so names never collide
    The user is expected to rename this placeholder afterward.
    """
    numbers = []
    for name in existing_names:
        m = _DEFAULT_TASK_NAME_RE.fullmatch(name)
        if m:
            numbers.append(int(m.group(1)))
    n = max(numbers) + 1 if numbers else 1
    return f"Task {n}"


def _seed_tasks() -> List[Task]:
    """Initial demo data.

    Due dates are decided relative to "the day the app was first launched".
    Under the default notification settings (notify_enabled=True /
    notify_days_before=3), they're arranged so the list tab's due-date
    highlighting shows "2 white, 2 yellow, 1 red" right from the start
    (yellow = due soon, red = overdue).

    Builds a fresh set of Task instances on every call (add_task rewrites
    task.id in place, so reusing the same Task objects across multiple
    TaskModel instances would cause id collisions).
    """
    today = date.today()

    def due(offset_days: int) -> str:
        return (today + timedelta(days=offset_days)).strftime("%Y-%m-%d")

    return [
        # Yellow: due soon (today+1 and today+2 are both within the today+3 warning threshold)
        Task("Prepare Quotation", "Sato", due(1), "High", "In Progress"),
        Task("Prepare Meeting Materials", "Tanaka", due(2), "Medium", "Not Started"),
        # Red: overdue (a past due date; turns red automatically while not yet done)
        Task("Write Release Notes", "Suzuki", due(-2), "High", "In Progress"),
        # White: Done tasks are always excluded from highlighting
        Task("Expense Report", "Sato", due(30), "Low", "Done"),
        # White: beyond the warning threshold (today+7 > today+3)
        Task("Design Review", "Tanaka", due(7), "Medium", "In Progress"),
    ]


class TaskModel:
    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        # Only seed demo data when "the DB file doesn't exist yet" = a
        # genuine first launch. connect() would create the file, so this
        # must be checked beforehand.
        # (":memory:" is a fresh disposable DB every time, so it's always
        # treated as a first run — used for tests.)
        first_run = db_path == ":memory:" or not Path(db_path).exists()

        self._conn = task_db.connect(db_path)
        self._tasks: List[Task] = task_db.fetch_all(self._conn)
        self._dirty = False
        if self._tasks:
            self._next_id = max(t.id for t in self._tasks) + 1
        else:
            self._next_id = 1
            if first_run:
                # First launch: seed the initial demo data and save immediately.
                # If the user later deletes every task, app.db still exists,
                # so it just stays empty — the demo data never comes back.
                for task in _seed_tasks():
                    self.add_task(task)
                self.save()

    def close(self) -> None:
        """Close the DB connection. It's fine for the app to leave it open
        until the process exits, but tests close it explicitly before
        removing their temp files (Windows in particular can't delete a
        file that's still open)."""
        self._conn.close()

    def list_tasks(self) -> List[Task]:
        """Return the list of registered tasks"""
        return list(self._tasks)

    def get_task(self, task_id: int) -> Optional[Task]:
        """Fetch a single task by id. Returns None if not found"""
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def is_dirty(self) -> bool:
        """Whether there are changes that haven't been save()d"""
        return self._dirty

    def save(self) -> None:
        """Flush the current in-memory state to the DB wholesale (used by the list tab's "Save" button)"""
        task_db.replace_all(self._conn, self._tasks)
        self._dirty = False

    def add_task(self, task: Task) -> Task:
        """Add one task. Assigns and returns its id (the DB isn't updated until save())"""
        task.id = self._next_id
        self._next_id += 1
        self._tasks.append(task)
        self._dirty = True
        return task

    def add_blank_task(self) -> Task:
        """Add one task with every field blank (used by the list tab's "add" button).

        Only the task name is not left blank — a placeholder "Task N" is
        used instead. N is the highest existing "Task <number>" value + 1
        (1 if none exist). Doesn't depend on the count or an id, so with
        only the seed data it starts at "Task 1", and it won't collide with
        an existing "Task N". The user is expected to rename it afterward.
        """
        name = _next_default_task_name(t.name for t in self._tasks)
        return self.add_task(
            Task(name=name, assignee="", due_date="", priority="", status="")
        )

    def delete_tasks(self, task_ids: Iterable[int]) -> None:
        """Delete the given tasks (used by the list tab's "delete" button; supports multi-select)"""
        ids = set(task_ids)
        self._tasks = [t for t in self._tasks if t.id not in ids]
        self._dirty = True

    def update_task_field(self, task_id: int, field: str, value: str) -> None:
        """Change a single field on the given task (used by the list tab's inline editing)"""
        if field not in EDITABLE_FIELDS:
            raise ValueError(f"Not an editable field: {field}")
        for task in self._tasks:
            if task.id == task_id:
                setattr(task, field, value)
                self._dirty = True
                return
        raise ValueError(f"No matching task found: id={task_id}")
