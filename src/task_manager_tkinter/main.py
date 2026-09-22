"""
Entry point
-----------
Loads model / view / presenter from their respective folders, wires them
together, and starts the app.
The folder hierarchy is directly the class namespace
(e.g. model/task/ <-> task_manager_tkinter.model.task.TaskModel).

Folder layout (file names describe the role; folder names are not repeated):
    src/task_manager_tkinter/     Root package (src layout)
        main.py          <- this file (same level as model, view, presenter)
        data/            Where the app's SQLite database (app.db) lives; created automatically at runtime
            backups/           Where automatic backups (last 24 hours), taken at the configured interval (default 15 min), are kept
        model/
            lib/            Pure I/O modules that hold no classes
                db_path.py        Default DB file path (shared by task/settings)
                db_backup.py      Backup and generation management for app.db (pure I/O)
                task_db.py        Task persistence (SQLite, pure I/O)
                settings_db.py    Settings persistence (SQLite, pure I/O)
                csv_io.py         CSV export/import (pure I/O)
            task/
                entity.py         Task (dataclass) + PRIORITIES / STATUSES
                store.py          TaskModel (holds the in-memory task collection and delegates persistence)
            settings/
                entity.py         Settings (dataclass)
                store.py          SettingsModel
        view/
            callbacks.py          CallbackRegistryMixin (callback-registration mixin shared by both tk_frames)
            task/
                contract.py       TaskListView (abstract class = the contract the Presenter depends on)
                tk_frame.py       Tkinter implementation (task list tab)
            settings/
                contract.py       SettingsView (abstract class = the contract the Presenter depends on)
                tk_frame.py       Tkinter implementation (settings tab)
            tk_main_window.py     Tkinter implementation (TkMainWindow, which combines the two tabs)
        presenter/            (one file per tab; no subfolders)
            task.py               TaskListPresenter
            settings.py           SettingsPresenter

How to run (either works):
    - From the repository root (puts src/ on the import path)
        PYTHONPATH=src python3 -m task_manager_tkinter.main
      or  cd src && python3 -m task_manager_tkinter.main
    - By file path directly
        python3 src/task_manager_tkinter/main.py
      or  cd src/task_manager_tkinter && python3 main.py
      (the sys.path bootstrap below makes absolute imports work)
* This is a GUI app, so run it on a machine that has Tcl/Tk available.
* Tasks and settings are persisted with SQLite (the sqlite3 standard library
  module, no extra install needed). The DB file is created as data/app.db
  on first run. Edits are always saved to the DB immediately (Auto Save).
  There is no Save button or "unsaved" indicator.
* At the interval specified in the "Backup" field of the Settings tab
  (default 15 minutes), the app checks whether app.db has changed and, if
  so, automatically takes a backup (skipped if nothing has changed since the
  last backup). Only the last 24 hours are kept; older backups are deleted
  automatically. This is a safety net in case the DB file itself becomes
  corrupted (e.g. due to disk failure).
  If the interval is changed while the app is running, the new interval
  takes effect starting from the next time the timer fires (an already
  scheduled tick is not cancelled and rescheduled immediately).
"""

import os
import sys

# When launched by file path (e.g. `python main.py` /
# `python src/task_manager_tkinter/main.py`), the task_manager_tkinter package
# is not yet on the import path at this point (__package__ is unset). Add the
# src layout's package parent = src/ (two levels above this file) to
# sys.path so the same absolute imports work as with
# `python -m task_manager_tkinter.main`. When launched with -m, __package__
# is already set, so this does nothing.
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

    # At the interval specified in the Settings tab (default 15 minutes), check
    # whether app.db has been modified since the last backup, and back it up if
    # so. This only compares the file's modification time (mtime), so it does
    # not distinguish which edit operation wrote it.
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
