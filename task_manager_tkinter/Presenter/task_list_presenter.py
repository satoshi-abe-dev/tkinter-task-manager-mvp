"""
Presenter — タスク一覧タブ
--------------------------
Modelのタスク一覧をViewに反映するだけの、シンプルな橋渡し役。
"""

from Model.task_model import TaskModel
from View.task_list_view import TaskListView


class TaskListPresenter:
    def __init__(self, model: TaskModel, view: TaskListView) -> None:
        self.model = model
        self.view = view
        self.refresh()

    def refresh(self) -> None:
        """Modelから最新のタスク一覧を取得し、Viewに反映する"""
        self.view.show_tasks(self.model.list_tasks())
