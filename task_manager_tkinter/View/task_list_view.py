"""
View（抽象層）— タスク一覧タブ
------------------------------
Presenterが依存する「契約」だけを定義する。
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional

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

    @abstractmethod
    def set_on_column_clicked(self, handler: Callable[[str], None]) -> None:
        """カラムのヘッダーがクリックされた時に呼ばれるハンドラを登録する。
        引数: field（クリックされた列名）
        """

    @abstractmethod
    def show_sort_state(self, field: Optional[str], ascending: bool) -> None:
        """現在のソート対象列・昇順/降順を見た目に反映する（列見出しの矢印など）。
        field が None の場合はソートされていない状態を表す。
        """
