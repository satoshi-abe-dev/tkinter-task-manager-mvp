"""
Presenter — タスク一覧タブ
--------------------------
Modelのタスク一覧をViewに反映する橋渡し役。
一覧のインライン編集・カラムヘッダークリックによるソートを扱う。
"""

from typing import Callable, Dict, List, Optional

from Model.task import PRIORITIES, STATUSES, Task
from Model.task_model import TaskModel
from View.task_list_view import TaskListView

_PRIORITY_ORDER = {value: index for index, value in enumerate(PRIORITIES)}
_STATUS_ORDER = {value: index for index, value in enumerate(STATUSES)}

# 列ごとのソートキー。優先度・ステータスは文字列の五十音順ではなく、
# Model.task で定義された意味のある並び順（低→高、未着手→完了 など）で並べる。
_SORT_KEYS: Dict[str, Callable[[Task], object]] = {
    "name": lambda t: t.name,
    "assignee": lambda t: t.assignee,
    "due_date": lambda t: t.due_date,
    "priority": lambda t: _PRIORITY_ORDER.get(t.priority, len(PRIORITIES)),
    "status": lambda t: _STATUS_ORDER.get(t.status, len(STATUSES)),
}


class TaskListPresenter:
    def __init__(self, model: TaskModel, view: TaskListView) -> None:
        self.model = model
        self.view = view
        self._sort_field: Optional[str] = None
        self._sort_ascending = True
        self.view.set_on_cell_edited(self.on_cell_edited)
        self.view.set_on_column_clicked(self.on_column_clicked)
        self.view.set_on_add_click(self.on_add_click)
        self.view.set_on_delete_click(self.on_delete_click)
        self.refresh()

    def refresh(self) -> None:
        """Modelから最新のタスク一覧を取得し、必要ならソートしてViewに反映する"""
        tasks = self.model.list_tasks()
        if self._sort_field is not None:
            key = _SORT_KEYS[self._sort_field]
            tasks.sort(key=key, reverse=not self._sort_ascending)
        self.view.show_tasks(tasks)
        self.view.show_sort_state(self._sort_field, self._sort_ascending)

    def on_cell_edited(self, task_id: int, field: str, value: str) -> None:
        """一覧タブでのインライン編集が確定した時に呼ばれる"""
        if field == "name" and not value.strip():
            # タスク名を空にはできない。編集前の表示に戻す。
            self.refresh()
            return
        self.model.update_task_field(task_id, field, value)
        self.refresh()

    def on_column_clicked(self, field: str) -> None:
        """一覧タブのカラムヘッダーがクリックされた時に呼ばれる"""
        if self._sort_field == field:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_field = field
            self._sort_ascending = True
        self.refresh()

    def on_add_click(self) -> None:
        """「追加」ボタン押下時に呼ばれる。空欄のタスクを1件追加して選択状態にする"""
        task = self.model.add_blank_task()
        self.refresh()
        self.view.select_task(task.id)

    def on_delete_click(self, task_ids: List[int]) -> None:
        """「削除」ボタン押下時に呼ばれる（確認ポップアップで「はい」が選ばれた後）。
        複数選択している場合は選択中の全件が渡される。
        """
        self.model.delete_tasks(task_ids)
        self.refresh()
