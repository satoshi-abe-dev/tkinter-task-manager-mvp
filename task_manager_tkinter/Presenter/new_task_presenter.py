"""
Presenter — 新規登録タブ
------------------------
入力値のバリデーション、Modelへの登録、登録後の一覧タブへの通知を行う。
"""

from typing import Callable

from Model.task import Task
from Model.task_model import TaskModel
from View.new_task_view import NewTaskView


class NewTaskPresenter:
    def __init__(
        self,
        model: TaskModel,
        view: NewTaskView,
        on_task_added: Callable[[], None],
    ) -> None:
        self.model = model
        self.view = view
        self.on_task_added = on_task_added
        self.view.set_on_register_click(self.on_register_click)
        self.view.set_on_cancel_click(self.on_cancel_click)

    def on_register_click(self) -> None:
        values = self.view.get_form_values()
        name = values["name"].strip()
        if not name:
            self.view.show_name_error("タスク名を入力してください")
            return

        self.view.show_name_error(None)
        task = Task(
            name=name,
            assignee=values["assignee"],
            due_date=values["due_date"],
            priority=values["priority"],
            status=values["status"],
            tags=[t.strip() for t in values["tags"].split(",") if t.strip()],
            memo=values["memo"],
        )
        self.model.add_task(task)
        self.view.clear_form()
        self.on_task_added()

    def on_cancel_click(self) -> None:
        self.view.clear_form()
        self.view.show_name_error(None)
