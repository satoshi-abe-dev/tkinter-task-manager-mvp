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
        """Register a handler for a committed inline edit: (task_id, field, new_value)"""

    @abstractmethod
    def set_on_column_clicked(self, handler: Callable[[str], None]) -> None:
        """Register a handler for a column-header click, given the field name"""

    @abstractmethod
    def show_sort_state(self, field: Optional[str], ascending: bool) -> None:
        """Reflect the current sort column/direction (e.g. header arrow).
        field=None means unsorted."""

    @abstractmethod
    def set_on_add_click(self, handler: Callable[[], None]) -> None:
        """Register a handler called when the "add" button is pressed"""

    @abstractmethod
    def set_on_delete_click(self, handler: Callable[[List[int]], None]) -> None:
        """Register a handler for the "delete" button, given the selected
        task_ids. Confirmation and row selection are the View's job — this
        fires only once "Yes" is chosen.
        """

    @abstractmethod
    def select_task(self, task_id: int) -> None:
        """Select the given task (e.g. after refreshing the list post-add)"""

    @abstractmethod
    def show_due_date_highlights(self, highlights: Dict[int, str]) -> None:
        """Highlight rows near/past due: task_id -> "warning"/"overdue".
        Ids not in the mapping return to normal display."""

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
