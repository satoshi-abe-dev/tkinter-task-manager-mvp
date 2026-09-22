"""
Task (dataclass)
-----------------
Represents the data for a single task. Holds no logic.
"""

from dataclasses import dataclass

# The possible values for priority and status, in their meaningful order
# (low to high, etc.). Shared by multiple places — form choices, list sort
# order, and so on. Status only covers workflow state. "Overdue" is not
# held as a status; it's derived each time from whether due_date is in the
# past, and highlighted in red (on the Presenter side).
PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Not Started", "In Progress", "Done"]


@dataclass
class Task:
    name: str
    assignee: str
    due_date: str
    priority: str  # "High" | "Medium" | "Low"
    status: str  # "Not Started" | "In Progress" | "Done"
    # Auto-assigned by TaskModel when a task is added; callers don't need to set it.
    # Used to reliably identify "which task" during inline editing in the
    # list (so it doesn't depend on the list's sort order or index).
    id: int = 0
