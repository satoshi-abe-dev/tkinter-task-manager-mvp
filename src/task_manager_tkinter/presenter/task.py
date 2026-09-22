"""
Presenter — task list tab
---------------------------
Bridges the Model's task list to the View.
Handles inline list editing, sorting by clicking a column header, and
highlighting tasks whose due date is approaching.
"""

import csv
from datetime import date, datetime, timedelta
from typing import Callable, Dict, List, Optional

from task_manager_tkinter.model.lib.csv_io import (
    export_tasks_to_csv,
    import_tasks_from_csv,
)
from task_manager_tkinter.model.settings import SettingsModel
from task_manager_tkinter.model.task import PRIORITIES, STATUSES, Task, TaskModel
from task_manager_tkinter.view.task import TaskListView

_PRIORITY_ORDER = {value: index for index, value in enumerate(PRIORITIES)}
_STATUS_ORDER = {value: index for index, value in enumerate(STATUSES)}

# Sort key per column. Priority and status are not sorted alphabetically;
# they use the meaningful order defined in model.task (low -> high,
# not-started -> done, etc.).
_SORT_KEYS: Dict[str, Callable[[Task], object]] = {
    "name": lambda t: t.name,
    "assignee": lambda t: t.assignee,
    "due_date": lambda t: t.due_date,
    "priority": lambda t: _PRIORITY_ORDER.get(t.priority, len(PRIORITIES)),
    "status": lambda t: _STATUS_ORDER.get(t.status, len(STATUSES)),
}

# Completed tasks are excluded from highlighting even if their due date has passed
_EXCLUDED_STATUS = "Done"


class TaskListPresenter:
    def __init__(
        self, model: TaskModel, settings_model: SettingsModel, view: TaskListView
    ) -> None:
        self.model = model
        self.settings_model = settings_model
        self.view = view
        self._sort_field: Optional[str] = None
        self._sort_ascending = True
        # Task id ordering used to keep "the order currently displayed" as-is,
        # ignoring column sort — e.g. right after an "add". While it is None,
        # tasks are re-sorted by _sort_field every time. Clearing it happens
        # when a column header is clicked.
        self._manual_order: Optional[List[int]] = None
        self.view.set_on_cell_edited(self.on_cell_edited)
        self.view.set_on_column_clicked(self.on_column_clicked)
        self.view.set_on_add_click(self.on_add_click)
        self.view.set_on_delete_click(self.on_delete_click)
        self.view.set_on_export_click(self.on_export_click)
        self.view.set_on_import_click(self.on_import_click)
        self.refresh()

    def refresh(self) -> None:
        """Fetch the latest task list from the Model, sort it if needed, and apply it to the View.

        If there are unsaved changes at this point, save() is called
        immediately (i.e. as a result, every edit operation is auto-saved —
        Auto Save).
        """
        tasks = self._ordered_tasks(self.model.list_tasks())
        self.view.show_tasks(tasks)
        self.view.show_sort_state(self._sort_field, self._sort_ascending)
        self.view.show_due_date_highlights(self._compute_due_date_highlights(tasks))
        if self.model.is_dirty():
            self.model.save()

    def _ordered_tasks(self, tasks: List[Task]) -> List[Task]:
        """Order the tasks in the current display order.
        Uses _manual_order (fixed order) if set, otherwise falls back to the
        result of the current sort column. Shared logic also used wherever
        "the current display order" is needed (e.g. when adding).
        """
        if self._manual_order is not None:
            return self._apply_manual_order(tasks)
        return self._sorted_tasks(tasks)

    def _sorted_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort the tasks according to the current sort column (left as-is if no column is set).

        Tasks with a blank value are always placed last, whether ascending
        or descending (with reverse=True, a plain key comparison alone would
        put blanks first, so "is it blank" needs to be handled separately).
        """
        if self._sort_field is None:
            return tasks
        field = self._sort_field
        key = _SORT_KEYS[field]
        tasks = sorted(tasks, key=key, reverse=not self._sort_ascending)
        # Since sorted() is a stable sort, sorting once more afterward by
        # just "is it blank" pushes only the blanks to the end while
        # preserving the order (ascending/descending result) of everything else.
        tasks = sorted(tasks, key=lambda t: not getattr(t, field).strip())
        return tasks

    def _apply_manual_order(self, tasks: List[Task]) -> List[Task]:
        """Apply the order fixed in _manual_order.

        Deleted task ids naturally drop out, and any new id not in
        _manual_order (e.g. added via import) is appended at the end.
        """
        tasks_by_id = {t.id: t for t in tasks}
        ordered_ids = [tid for tid in self._manual_order if tid in tasks_by_id]
        known_ids = set(ordered_ids)
        ordered_ids += [t.id for t in tasks if t.id not in known_ids]
        self._manual_order = ordered_ids
        return [tasks_by_id[tid] for tid in ordered_ids]

    def _compute_due_date_highlights(self, tasks: List[Task]) -> Dict[int, str]:
        """Build an id -> kind mapping for highlighting tasks whose due date is near or past.

        Uses the Settings tab's notification settings (enabled/disabled, how
        many days ahead to warn) as-is for the judgment. No highlighting
        while notifications are disabled.
        """
        settings = self.settings_model.get()
        if not settings.notify_enabled:
            return {}

        today = date.today()
        warning_cutoff = today + timedelta(days=settings.notify_days_before)

        highlights: Dict[int, str] = {}
        for task in tasks:
            if task.status == _EXCLUDED_STATUS:
                continue
            try:
                due = datetime.strptime(task.due_date, "%Y-%m-%d").date()
            except ValueError:
                continue  # Don't highlight tasks with no/unparseable due date
            if due < today:
                highlights[task.id] = "overdue"  # Overdue (= red) is decided solely here
            elif due <= warning_cutoff:
                highlights[task.id] = "warning"
        return highlights

    def on_cell_edited(self, task_id: int, field: str, value: str) -> None:
        """Called when an inline edit on the list tab is committed"""
        if field == "name" and not value.strip():
            # Task name can't be blank. Revert to the pre-edit display.
            self.refresh()
            return
        self.model.update_task_field(task_id, field, value)
        self.refresh()

    def on_column_clicked(self, field: str) -> None:
        """Called when a column header on the list tab is clicked"""
        self._manual_order = None  # An explicit column-sort action, so clear the fixed order
        if self._sort_field == field:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_field = field
            self._sort_ascending = True
        self.refresh()

    def on_add_click(self) -> None:
        """Called when the "add" button is pressed. Adds one blank task and selects it.

        Keeps the current row order as displayed (the sort result if
        sorting, or the already-fixed order if _manual_order is set) and
        only appends the new task at the end. Using _sorted_tasks() alone
        would cause a second (or later) add to ignore the order fixed by a
        previous add (because _sort_field is already None by the time of the
        first add), so _ordered_tasks() is used instead, which also takes
        _manual_order into account. The column header's sort arrow is hidden
        to show that it's no longer strictly sorted.
        """
        current_order = [t.id for t in self._ordered_tasks(self.model.list_tasks())]
        task = self.model.add_blank_task()
        self._manual_order = current_order + [task.id]
        self._sort_field = None
        self.refresh()
        self.view.select_task(task.id)

    def on_delete_click(self, task_ids: List[int]) -> None:
        """Called when the "delete" button is pressed (after "Yes" is chosen in the confirmation popup).
        If multiple rows are selected, every selected id is passed in.
        """
        self.model.delete_tasks(task_ids)
        self.refresh()

    def on_export_click(self) -> None:
        """Called when the "export" button is pressed"""
        path = self.view.ask_save_path()
        if not path:
            return
        try:
            export_tasks_to_csv(self.model.list_tasks(), path)
        except (OSError, csv.Error) as exc:
            # Can't write, disk full, etc. Report it instead of a raw traceback.
            self.view.show_message("Error", f"Could not export the CSV file.\n{exc}")
            return
        self.view.show_message("Notice", f"Exported to {path}")

    def on_import_click(self) -> None:
        """Called when the "import" button is pressed"""
        path = self.view.ask_open_path()
        if not path:
            return
        try:
            tasks, skipped = import_tasks_from_csv(path)
        except (OSError, csv.Error, ValueError) as exc:
            # File can't be opened, malformed CSV, bad encoding, missing column, etc.
            # (UnicodeDecodeError is a subclass of ValueError, so it's caught here too)
            self.view.show_message("Error", f"Could not import the CSV file.\n{exc}")
            return
        for task in tasks:
            self.model.add_task(task)
        self.refresh()

        message = f"Imported {len(tasks)} task(s)"
        if skipped:
            message += f" ({skipped} skipped due to missing task name)"
        self.view.show_message("Notice", message)
