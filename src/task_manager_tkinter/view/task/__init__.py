"""
view.task — View layer for the task list tab. The folder = this namespace.

Only re-exports the abstract TaskListView (contract.py). Re-exporting the Tk
implementation here would drag tkinter into every import of this package,
breaking test_presenter.py's tkinter-free assumption — import
`task_manager_tkinter.view.task.tk_frame` directly instead.
"""

from task_manager_tkinter.view.task.contract import TaskListView

__all__ = ["TaskListView"]
