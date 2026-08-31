"""
Task（データクラス）
--------------------
タスク1件分のデータを表す。ロジックは持たない。
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    name: str
    assignee: str
    due_date: str
    priority: str  # "高" | "中" | "低"
    status: str  # "未着手" | "進行中" | "完了" | "遅延"
    tags: List[str] = field(default_factory=list)
    memo: str = ""
