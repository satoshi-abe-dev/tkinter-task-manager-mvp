"""model.task — Domain layer for tasks. The folder = this namespace."""

from task_manager_tkinter.model.task.entity import PRIORITIES, STATUSES, Task
from task_manager_tkinter.model.task.store import EDITABLE_FIELDS, TaskModel

__all__ = ["PRIORITIES", "STATUSES", "Task", "TaskModel", "EDITABLE_FIELDS"]
