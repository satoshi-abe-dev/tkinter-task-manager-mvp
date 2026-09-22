"""
Model — task persistence (SQLite)
------------------------------------
Pure I/O logic, with no dependency on tkinter, for saving and loading tasks
to/from SQLite. It plays the same role as csv_io.py: TaskModel
(model/task/store.py) reads and writes the DB through this module.

Rather than writing "one row per edit", writes use a snapshot approach:
whenever TaskModel.save() is called, the current in-memory state is written
to the DB wholesale. This ensures nothing is written to disk until the user
explicitly presses the "Save" button (so if you make a mistake before
saving, as long as you don't save, restarting the app puts you right back
to the last saved state).
"""

import sqlite3
from pathlib import Path
from typing import List

from task_manager_tkinter.model.lib.db_path import DEFAULT_DB_PATH
from task_manager_tkinter.model.task.entity import Task

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    assignee TEXT NOT NULL,
    due_date TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL
)
"""


def connect(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Connect to the DB file, creating the file/table if they don't exist.

    Passing db_path=":memory:" gives an in-memory DB that isn't written to
    disk (for tests — each call gets an independent, empty DB, so state
    doesn't bleed between tests).
    """
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(_CREATE_TABLE_SQL)
    conn.commit()
    return conn


def fetch_all(conn: sqlite3.Connection) -> List[Task]:
    """Fetch every saved task (ordered by id ascending = insertion order)"""
    rows = conn.execute(
        "SELECT id, name, assignee, due_date, priority, status FROM tasks ORDER BY id"
    ).fetchall()
    return [
        Task(id=r[0], name=r[1], assignee=r[2], due_date=r[3], priority=r[4], status=r[5])
        for r in rows
    ]


def replace_all(conn: sqlite3.Connection, tasks: List[Task]) -> None:
    """Replace the DB's contents wholesale with the given task list (for the "Save" operation).

    No diffing — simply deletes every existing row and reinserts them all
    (plenty fast at the scale of a task-manager app). id is written
    explicitly too, so that ids assigned by TaskModel for existing tasks are
    preserved as-is.
    """
    conn.execute("DELETE FROM tasks")
    conn.executemany(
        "INSERT INTO tasks (id, name, assignee, due_date, priority, status) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [(t.id, t.name, t.assignee, t.due_date, t.priority, t.status) for t in tasks],
    )
    conn.commit()
