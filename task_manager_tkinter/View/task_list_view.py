"""
View（抽象層）— タスク一覧タブ
------------------------------
Presenterが依存する「契約」だけを定義する。
"""

from abc import ABC, abstractmethod
from typing import Callable, List

from Model.task import Task


class TaskListView(ABC):
    @abstractmethod
    def show_tasks(self, tasks: List[Task]) -> None:
        """タスク一覧を表示する"""

    @abstractmethod
    def set_on_cell_edited(
        self, handler: Callable[[int, str, str], None]
    ) -> None:
        """セルのインライン編集が確定した時に呼ばれるハンドラを登録する。
        引数: (task_id, field, new_value)
        """
