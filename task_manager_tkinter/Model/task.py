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
    # TaskModelが追加時に自動採番する。呼び出し側は指定しなくてよい。
    # 一覧のインライン編集時に「どのタスクか」を安定して特定するために使う
    # （一覧の並び順やインデックスに依存させないため）。
    id: int = 0
