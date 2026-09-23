"""
Task (dataclass)
-----------------
Represents the data for a single task. Holds no logic.
"""

from dataclasses import dataclass

# Meaningful order (low to high), shared by form choices and list sort.
# "Overdue" isn't a status — it's derived from due_date on the Presenter side.
PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Not Started", "In Progress", "Done"]


@dataclass
class Task:
    name: str
    assignee: str
    due_date: str
    priority: str  # "High" | "Medium" | "Low"
    status: str  # "Not Started" | "In Progress" | "Done"
    # Auto-assigned by TaskModel; identifies a row independent of sort/index.
    id: int = 0
