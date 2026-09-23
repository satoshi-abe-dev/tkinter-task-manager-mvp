"""
Entry point
-----------
Loads model / view / presenter, wires them together, and starts the app.
Folder hierarchy = class namespace; full tree in README's Design section.

Run: `PYTHONPATH=src python3 -m task_manager_tkinter.main` from the repo
root, or `python3 src/task_manager_tkinter/main.py` directly (the sys.path
bootstrap below makes absolute imports work either way). Needs Tcl/Tk.

Persistence: SQLite, auto-saved on every edit (no Save button). Backups run
on the Settings tab's interval (default 15 min), skipped if app.db hasn't
changed, keeping only the last 24 hours.
"""

import os
import sys

# Run by file path (not -m): __package__ is unset, so the package isn't
# importable yet. Add src/ (two levels up) to sys.path so absolute imports
# still work. No-op when run with -m.
if __package__ in (None, ""):
    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

from task_manager_tkinter.model.lib.db_backup import backup_and_rotate  # noqa: E402
from task_manager_tkinter.model.lib.db_path import DEFAULT_DB_PATH  # noqa: E402
from task_manager_tkinter.model.settings import SettingsModel  # noqa: E402
from task_manager_tkinter.model.task import TaskModel  # noqa: E402
from task_manager_tkinter.presenter.settings import SettingsPresenter  # noqa: E402
from task_manager_tkinter.presenter.task import TaskListPresenter  # noqa: E402
from task_manager_tkinter.view.tk_main_window import TkMainWindow  # noqa: E402

_MIN_BACKUP_INTERVAL_MINUTES = 1  # Lower bound so a value <= 0 can't cause runaway backups


def main() -> None:
    task_model = TaskModel()
    settings_model = SettingsModel()

    window = TkMainWindow()

    task_list_presenter = TaskListPresenter(task_model, settings_model, window.task_list_frame)
    SettingsPresenter(
        settings_model,
        window.settings_frame,
        on_settings_saved=task_list_presenter.refresh,
    )

    # Backs up only when app.db's mtime changed since the last check
    last_backup_mtime = None

    def check_and_backup() -> None:
        nonlocal last_backup_mtime
        if os.path.exists(DEFAULT_DB_PATH):
            current_mtime = os.path.getmtime(DEFAULT_DB_PATH)
            if current_mtime != last_backup_mtime:
                backup_and_rotate(DEFAULT_DB_PATH)
                last_backup_mtime = current_mtime
        interval_minutes = max(
            _MIN_BACKUP_INTERVAL_MINUTES, settings_model.get().backup_interval_minutes
        )
        window.schedule(interval_minutes * 60 * 1000, check_and_backup)

    initial_interval_minutes = max(
        _MIN_BACKUP_INTERVAL_MINUTES, settings_model.get().backup_interval_minutes
    )
    window.schedule(initial_interval_minutes * 60 * 1000, check_and_backup)

    window.run()


if __name__ == "__main__":
    main()
