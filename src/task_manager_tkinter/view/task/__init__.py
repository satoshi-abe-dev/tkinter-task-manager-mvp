"""
view.task — View layer for the task list tab. The folder = this namespace.

Only re-exports the abstract class TaskListView (contract.py). Importing the
Tkinter implementation (TkTaskListFrame) here would drag tkinter in just from
reading `task_manager_tkinter.view.task` for the abstract View (breaking
test_presenter.py's assumption that it runs without tkinter), so import the
Tk implementation via its full module path,
`task_manager_tkinter.view.task.tk_frame`, instead.
"""

from task_manager_tkinter.view.task.contract import TaskListView

__all__ = ["TaskListView"]
