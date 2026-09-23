"""
Model — settings persistence (SQLite)
----------------------------------------
Pure I/O, no tkinter dependency. Exchanges primitive values, not the
Settings dataclass (model.settings.entity) — avoids a circular import.
"""

import sqlite3
from pathlib import Path
from typing import Tuple

from task_manager_tkinter.model.lib.db_path import DEFAULT_DB_PATH

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    notify_enabled INTEGER NOT NULL,
    notify_days_before INTEGER NOT NULL,
    backup_interval_minutes INTEGER NOT NULL
)
"""

# settings is a single-row table; it always reuses the one row (id=1).
_DEFAULT_NOTIFY_ENABLED = True
_DEFAULT_NOTIFY_DAYS_BEFORE = 3
_DEFAULT_BACKUP_INTERVAL_MINUTES = 15


def connect(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Connect to the DB file, creating the file/table if they don't exist.
    Passing db_path=":memory:" gives a disposable DB for tests.
    """
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(_CREATE_TABLE_SQL)
    conn.commit()
    return conn


def load(conn: sqlite3.Connection) -> Tuple[bool, int, int]:
    """Load the settings. If the row doesn't exist yet, create one with the
    default values first, then return it (on first launch).
    Returns: (notify_enabled, notify_days_before, backup_interval_minutes)
    """
    row = conn.execute(
        "SELECT notify_enabled, notify_days_before, backup_interval_minutes "
        "FROM settings WHERE id = 1"
    ).fetchone()
    if row is None:
        save(
            conn,
            _DEFAULT_NOTIFY_ENABLED,
            _DEFAULT_NOTIFY_DAYS_BEFORE,
            _DEFAULT_BACKUP_INTERVAL_MINUTES,
        )
        return (
            _DEFAULT_NOTIFY_ENABLED,
            _DEFAULT_NOTIFY_DAYS_BEFORE,
            _DEFAULT_BACKUP_INTERVAL_MINUTES,
        )
    return bool(row[0]), int(row[1]), int(row[2])


def save(
    conn: sqlite3.Connection,
    notify_enabled: bool,
    notify_days_before: int,
    backup_interval_minutes: int,
) -> None:
    """Save the settings (since there's only ever one row, replace it wholesale with INSERT OR REPLACE)"""
    conn.execute(
        "INSERT OR REPLACE INTO settings "
        "(id, notify_enabled, notify_days_before, backup_interval_minutes) VALUES (1, ?, ?, ?)",
        (int(notify_enabled), notify_days_before, backup_interval_minutes),
    )
    conn.commit()
