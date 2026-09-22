"""
The default path to the SQLite database file used by the whole app.
TaskModel and SettingsModel each open this same file with their own
independent connection, reading and writing the tasks table and the
settings table respectively (neither knows the other exists).

In tests (test_presenter.py), ":memory:" is passed instead of this default
path, giving a disposable DB that leaves nothing on disk (so state doesn't
bleed between tests).
"""

from pathlib import Path

# src/task_manager_tkinter/data/app.db
# Based on this file's own location so it doesn't depend on the current
# working directory. This file lives at src/task_manager_tkinter/model/lib/,
# so going up 3 parents reaches the package root (src/task_manager_tkinter/).
DEFAULT_DB_PATH = str(
    Path(__file__).resolve().parent.parent.parent / "data" / "app.db"
)
