"""
View（抽象層）— タスク一覧タブ
------------------------------
Presenterが依存する「契約」だけを定義する。
"""

from abc import ABC, abstractmethod
from typing import List

from Model.task import Task


class TaskListView(ABC):
    @abstractmethod
    def show_tasks(self, tasks: List[Task]) -> None:
        """タスク一覧を表示する"""
