"""
Presenterの単体テスト例
-----------------------
FakeView（各View抽象クラスの偽実装）を差し込むことで、Tkinterを一切起動せずに
3つのPresenterのロジックを検証する。View.tk_main_window（Tkinter実装）は
読み込まないため、tkinterがインストールされていない環境でもこのテストは実行できる。

実行方法:
    このフォルダ(task_manager_tkinter)の直下で
        python3 test_presenter.py
"""

import os
import tempfile
from typing import Callable, List, Optional, Tuple

from Model.settings_model import Settings, SettingsModel
from Model.task import Task
from Model.task_model import TaskModel
from Presenter.new_task_presenter import NewTaskPresenter
from Presenter.settings_presenter import SettingsPresenter
from Presenter.task_list_presenter import TaskListPresenter
from View.new_task_view import NewTaskView
from View.settings_view import SettingsView
from View.task_list_view import TaskListView


class FakeTaskListView(TaskListView):
    def __init__(self) -> None:
        self.shown_tasks: List[Task] = []
        self.cell_edited_handler: Optional[Callable[[int, str, str], None]] = None
        self.column_clicked_handler: Optional[Callable[[str], None]] = None
        self.sort_state: Optional[Tuple[Optional[str], bool]] = None

    def show_tasks(self, tasks: List[Task]) -> None:
        self.shown_tasks = list(tasks)

    def set_on_cell_edited(self, handler: Callable[[int, str, str], None]) -> None:
        self.cell_edited_handler = handler

    def set_on_column_clicked(self, handler: Callable[[str], None]) -> None:
        self.column_clicked_handler = handler

    def show_sort_state(self, field: Optional[str], ascending: bool) -> None:
        self.sort_state = (field, ascending)


class FakeNewTaskView(NewTaskView):
    def __init__(self) -> None:
        self.register_handler: Optional[Callable[[], None]] = None
        self.cancel_handler: Optional[Callable[[], None]] = None
        self.form_values: dict = {
            "name": "",
            "assignee": "佐藤",
            "due_date": "",
            "priority": "中",
            "status": "未着手",
            "tags": "",
            "memo": "",
        }
        self.name_error: Optional[str] = None
        self.cleared = False

    def set_on_register_click(self, handler: Callable[[], None]) -> None:
        self.register_handler = handler

    def set_on_cancel_click(self, handler: Callable[[], None]) -> None:
        self.cancel_handler = handler

    def get_form_values(self) -> dict:
        return self.form_values

    def show_name_error(self, message: Optional[str]) -> None:
        self.name_error = message

    def clear_form(self) -> None:
        self.cleared = True


class FakeSettingsView(SettingsView):
    def __init__(self) -> None:
        self.field_changed_handler: Optional[Callable[[], None]] = None
        self.save_handler: Optional[Callable[[], None]] = None
        self.export_handler: Optional[Callable[[], None]] = None
        self.import_handler: Optional[Callable[[], None]] = None
        self.loaded: Optional[Settings] = None
        self.dirty = False
        self.form_values = Settings()
        self.save_path: Optional[str] = None
        self.open_path: Optional[str] = None
        self.messages: List[Tuple[str, str]] = []

    def set_on_field_changed(self, handler: Callable[[], None]) -> None:
        self.field_changed_handler = handler

    def set_on_save_click(self, handler: Callable[[], None]) -> None:
        self.save_handler = handler

    def set_on_export_click(self, handler: Callable[[], None]) -> None:
        self.export_handler = handler

    def set_on_import_click(self, handler: Callable[[], None]) -> None:
        self.import_handler = handler

    def load_settings(self, settings: Settings) -> None:
        self.loaded = settings

    def get_form_values(self) -> Settings:
        return self.form_values

    def set_dirty(self, dirty: bool) -> None:
        self.dirty = dirty

    def ask_save_path(self) -> Optional[str]:
        return self.save_path

    def ask_open_path(self) -> Optional[str]:
        return self.open_path

    def show_message(self, title: str, message: str) -> None:
        self.messages.append((title, message))


def test_task_list_presenter_shows_initial_tasks() -> None:
    model = TaskModel()
    view = FakeTaskListView()
    TaskListPresenter(model, view)

    assert len(view.shown_tasks) == len(model.list_tasks())
    print("test_task_list_presenter_shows_initial_tasks: OK")


def test_task_list_presenter_edits_cell() -> None:
    model = TaskModel()
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, view)

    target = model.list_tasks()[0]
    view.cell_edited_handler(target.id, "assignee", "鈴木")

    assert model.list_tasks()[0].assignee == "鈴木"
    # 更新後にViewへ再表示されている
    assert view.shown_tasks[0].assignee == "鈴木"
    print("test_task_list_presenter_edits_cell: OK")


def test_task_list_presenter_rejects_empty_name_edit() -> None:
    model = TaskModel()
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, view)

    target = model.list_tasks()[0]
    original_name = target.name
    view.cell_edited_handler(target.id, "name", "   ")

    assert model.list_tasks()[0].name == original_name
    print("test_task_list_presenter_rejects_empty_name_edit: OK")


def test_task_list_presenter_sorts_by_column_and_toggles_direction() -> None:
    model = TaskModel()
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, view)

    assert view.sort_state == (None, True)  # 初期状態はソートなし

    view.column_clicked_handler("due_date")
    dates = [t.due_date for t in view.shown_tasks]
    assert dates == sorted(dates)  # 昇順
    assert view.sort_state == ("due_date", True)

    view.column_clicked_handler("due_date")  # 同じ列を再クリック→降順に切り替え
    dates = [t.due_date for t in view.shown_tasks]
    assert dates == sorted(dates, reverse=True)
    assert view.sort_state == ("due_date", False)

    view.column_clicked_handler("name")  # 別の列をクリック→昇順から
    assert view.sort_state == ("name", True)
    print("test_task_list_presenter_sorts_by_column_and_toggles_direction: OK")


def test_task_list_presenter_sorts_priority_by_meaning_not_alphabetically() -> None:
    model = TaskModel()
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, view)

    view.column_clicked_handler("priority")

    priorities = [t.priority for t in view.shown_tasks]
    assert priorities == ["低", "中", "中", "高", "高"]
    print("test_task_list_presenter_sorts_priority_by_meaning_not_alphabetically: OK")


def test_new_task_presenter_rejects_empty_name() -> None:
    model = TaskModel()
    view = FakeNewTaskView()
    NewTaskPresenter(model, view, on_task_added=lambda: None)

    before = len(model.list_tasks())
    view.form_values["name"] = "   "
    view.register_handler()

    assert view.name_error == "タスク名を入力してください"
    assert len(model.list_tasks()) == before
    print("test_new_task_presenter_rejects_empty_name: OK")


def test_new_task_presenter_adds_task_and_notifies() -> None:
    model = TaskModel()
    view = FakeNewTaskView()
    added: List[bool] = []
    NewTaskPresenter(model, view, on_task_added=lambda: added.append(True))

    before = len(model.list_tasks())
    view.form_values.update({"name": "新規タスク", "tags": "経理, 月次"})
    view.register_handler()

    assert view.name_error is None
    assert view.cleared is True
    assert len(added) == 1
    assert len(model.list_tasks()) == before + 1

    new_task = model.list_tasks()[-1]
    assert new_task.name == "新規タスク"
    assert new_task.tags == ["経理", "月次"]
    print("test_new_task_presenter_adds_task_and_notifies: OK")


def test_new_task_presenter_cancel_clears_form() -> None:
    model = TaskModel()
    view = FakeNewTaskView()
    NewTaskPresenter(model, view, on_task_added=lambda: None)

    view.cancel_handler()
    assert view.cleared is True
    print("test_new_task_presenter_cancel_clears_form: OK")


def test_settings_presenter_tracks_dirty_and_saves() -> None:
    settings_model = SettingsModel()
    task_model = TaskModel()
    view = FakeSettingsView()
    SettingsPresenter(settings_model, task_model, view, on_tasks_imported=lambda: None)

    assert view.loaded == Settings()
    assert view.dirty is False

    view.field_changed_handler()
    assert view.dirty is True

    view.form_values = Settings(
        notify_enabled=False,
        notify_days_before=7,
        default_assignee="佐藤",
        page_size=50,
        theme="ダーク",
    )
    view.save_handler()

    assert view.dirty is False
    assert settings_model.get().theme == "ダーク"
    print("test_settings_presenter_tracks_dirty_and_saves: OK")


def test_settings_presenter_export_import_csv() -> None:
    settings_model = SettingsModel()
    task_model = TaskModel()
    view = FakeSettingsView()
    imported: List[bool] = []
    SettingsPresenter(
        settings_model, task_model, view, on_tasks_imported=lambda: imported.append(True)
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "tasks.csv")

        view.save_path = path
        view.export_handler()
        assert os.path.exists(path)

        before = len(task_model.list_tasks())
        view.open_path = path
        view.import_handler()

        assert len(imported) == 1
        assert len(task_model.list_tasks()) == before * 2
        # 書き出し・読み込みそれぞれで1件ずつメッセージが表示される
        assert len(view.messages) == 2
    print("test_settings_presenter_export_import_csv: OK")


if __name__ == "__main__":
    test_task_list_presenter_shows_initial_tasks()
    test_task_list_presenter_edits_cell()
    test_task_list_presenter_rejects_empty_name_edit()
    test_task_list_presenter_sorts_by_column_and_toggles_direction()
    test_task_list_presenter_sorts_priority_by_meaning_not_alphabetically()
    test_new_task_presenter_rejects_empty_name()
    test_new_task_presenter_adds_task_and_notifies()
    test_new_task_presenter_cancel_clears_form()
    test_settings_presenter_tracks_dirty_and_saves()
    test_settings_presenter_export_import_csv()
