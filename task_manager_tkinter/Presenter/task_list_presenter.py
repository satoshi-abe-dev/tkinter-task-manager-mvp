"""
Presenter — タスク一覧タブ
--------------------------
Modelのタスク一覧をViewに反映する橋渡し役。
一覧のインライン編集・カラムヘッダークリックによるソート・期限接近のハイライトを扱う。
"""

from datetime import date, datetime, timedelta
from typing import Callable, Dict, List, Optional

from Model.settings_model import SettingsModel
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

# 完了したタスクは、期限が過ぎていてもハイライト対象から除外する
_EXCLUDED_STATUS = "完了"


class TaskListPresenter:
    def __init__(
        self, model: TaskModel, settings_model: SettingsModel, view: TaskListView
    ) -> None:
        self.model = model
        self.settings_model = settings_model
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
        self.view.show_due_date_highlights(self._compute_due_date_highlights(tasks))

    def _compute_due_date_highlights(self, tasks: List[Task]) -> Dict[int, str]:
        """期限が近い/過ぎているタスクをハイライトするための、id→種別の対応表を作る。

        「設定」タブの通知設定（有効/無効・何日前から知らせるか）をそのまま
        判定基準として使う。通知が無効になっている間はハイライトしない。
        """
        settings = self.settings_model.get()
        if not settings.notify_enabled:
            return {}

        today = date.today()
        warning_cutoff = today + timedelta(days=settings.notify_days_before)

        highlights: Dict[int, str] = {}
        for task in tasks:
            if task.status == _EXCLUDED_STATUS:
                continue
            try:
                due = datetime.strptime(task.due_date, "%Y-%m-%d").date()
            except ValueError:
                continue  # 期限未設定・解釈できない値はハイライトしない
            if due < today:
                highlights[task.id] = "overdue"
            elif due <= warning_cutoff:
                highlights[task.id] = "warning"
        return highlights

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
