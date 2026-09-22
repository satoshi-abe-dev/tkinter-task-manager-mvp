"""
View (abstract layer) — task list tab
-----------------------------------------
Defines only the "contract" the Presenter depends on.
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional

from task_manager_tkinter.model.task import Task


class TaskListView(ABC):
    @abstractmethod
    def show_tasks(self, tasks: List[Task]) -> None:
        """Display the task list"""

    @abstractmethod
    def set_on_cell_edited(
        self, handler: Callable[[int, str, str], None]
    ) -> None:
        """Register a handler called when an inline cell edit is committed.
        Arguments: (task_id, field, new_value)
        """

    @abstractmethod
    def set_on_column_clicked(self, handler: Callable[[str], None]) -> None:
        """Register a handler called when a column header is clicked.
        Argument: field (the name of the clicked column)
        """

    @abstractmethod
    def show_sort_state(self, field: Optional[str], ascending: bool) -> None:
        """Reflect the current sort column and ascending/descending direction
        visually (e.g. the arrow on the column header).
        field == None represents the unsorted state.
        """

    @abstractmethod
    def set_on_add_click(self, handler: Callable[[], None]) -> None:
        """Register a handler called when the "add" button is pressed"""

    @abstractmethod
    def set_on_delete_click(self, handler: Callable[[List[int]], None]) -> None:
        """Register a handler called when the "delete" button is pressed.
        Argument: task_ids (the targets to delete; every selected id if
        multiple rows are selected).
        Showing the confirmation popup and identifying the selected rows is
        the View's responsibility; this handler is only called once "Yes" is chosen.
        """

    @abstractmethod
    def select_task(self, task_id: int) -> None:
        """Select the given task (used e.g. after refreshing the list right after an add)"""

    @abstractmethod
    def show_due_date_highlights(self, highlights: Dict[int, str]) -> None:
        """Visually emphasize rows for tasks whose due date is near or past.
        Argument: a task_id -> "warning" (due soon) or "overdue" (past due) mapping.
        Any task_id not in the mapping is returned to normal display.
        """

    @abstractmethod
    def set_on_export_click(self, handler: Callable[[], None]) -> None:
        """Register a handler called when the "export" button is pressed"""

    @abstractmethod
    def set_on_import_click(self, handler: Callable[[], None]) -> None:
        """Register a handler called when the "import" button is pressed"""

    @abstractmethod
    def ask_save_path(self) -> Optional[str]:
        """Let the user choose the export destination file path. None if cancelled"""

    @abstractmethod
    def ask_open_path(self) -> Optional[str]:
        """Let the user choose the import source file path. None if cancelled"""

    @abstractmethod
    def show_message(self, title: str, message: str) -> None:
        """Show a message in a popup"""
