"""
Presenter — タスク一覧タブ
--------------------------
Modelのタスク一覧をViewに反映する橋渡し役。
一覧のインライン編集が確定した時に、Modelを更新して再描画する。
"""

from Model.task_model import TaskModel
from View.task_list_view import TaskListView


class TaskListPresenter:
    def __init__(self, model: TaskModel, view: TaskListView) -> None:
        self.model = model
        self.view = view
        self.view.set_on_cell_edited(self.on_cell_edited)
        self.refresh()

    def refresh(self) -> None:
        """Modelから最新のタスク一覧を取得し、Viewに反映する"""
        self.view.show_tasks(self.model.list_tasks())

    def on_cell_edited(self, task_id: int, field: str, value: str) -> None:
        """一覧タブでのインライン編集が確定した時に呼ばれる"""
        if field == "name" and not value.strip():
            # タスク名を空にはできない。編集前の表示に戻す。
            self.refresh()
            return
        self.model.update_task_field(task_id, field, value)
        self.refresh()
