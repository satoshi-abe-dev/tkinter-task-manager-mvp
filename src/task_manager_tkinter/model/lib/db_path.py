"""
Default SQLite path for the whole app. TaskModel and SettingsModel each
open it with their own connection (tasks / settings tables, unaware of
each other). Tests pass ":memory:" instead, for a disposable DB.
"""

from pathlib import Path

# src/task_manager_tkinter/data/app.db — relative to this file, not cwd
DEFAULT_DB_PATH = str(
    Path(__file__).resolve().parent.parent.parent / "data" / "app.db"
)
