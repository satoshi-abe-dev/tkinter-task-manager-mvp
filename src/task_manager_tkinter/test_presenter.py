"""
Presenter unit tests (pytest)
--------------------------------
Verifies both Presenters without starting Tkinter, via a FakeView per View
ABC. Doesn't import the Tkinter View implementations, so it runs without
tkinter installed.

    pip install -r requirements-dev.txt && pytest
"""

import os
import tempfile
from datetime import date, datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple

import pytest

from task_manager_tkinter.model.lib.db_backup import backup_and_rotate
from task_manager_tkinter.model.settings import Settings, SettingsModel
from task_manager_tkinter.model.task import Task, TaskModel
from task_manager_tkinter.model.task.store import _next_default_task_name
from task_manager_tkinter.presenter.settings import SettingsPresenter
from task_manager_tkinter.presenter.task import TaskListPresenter
from task_manager_tkinter.view.settings import SettingsView
from task_manager_tkinter.view.task import TaskListView


class FakeTaskListView(TaskListView):
    def __init__(self) -> None:
        self.shown_tasks: List[Task] = []
        self.cell_edited_handler: Optional[Callable[[int, str, str], None]] = None
        self.column_clicked_handler: Optional[Callable[[str], None]] = None
        self.add_handler: Optional[Callable[[], None]] = None
        self.delete_handler: Optional[Callable[[List[int]], None]] = None
        self.export_handler: Optional[Callable[[], None]] = None
        self.import_handler: Optional[Callable[[], None]] = None
        self.sort_state: Optional[Tuple[Optional[str], bool]] = None
        self.selected_task_id: Optional[int] = None
        self.highlights: Dict[int, str] = {}
        self.save_path: Optional[str] = None
        self.open_path: Optional[str] = None
        self.messages: List[Tuple[str, str]] = []

    def show_tasks(self, tasks: List[Task]) -> None:
        self.shown_tasks = list(tasks)

    def set_on_cell_edited(self, handler: Callable[[int, str, str], None]) -> None:
        self.cell_edited_handler = handler

    def set_on_column_clicked(self, handler: Callable[[str], None]) -> None:
        self.column_clicked_handler = handler

    def show_sort_state(self, field: Optional[str], ascending: bool) -> None:
        self.sort_state = (field, ascending)

    def set_on_add_click(self, handler: Callable[[], None]) -> None:
        self.add_handler = handler

    def set_on_delete_click(self, handler: Callable[[List[int]], None]) -> None:
        self.delete_handler = handler

    def select_task(self, task_id: int) -> None:
        self.selected_task_id = task_id

    def show_due_date_highlights(self, highlights: Dict[int, str]) -> None:
        self.highlights = dict(highlights)

    def set_on_export_click(self, handler: Callable[[], None]) -> None:
        self.export_handler = handler

    def set_on_import_click(self, handler: Callable[[], None]) -> None:
        self.import_handler = handler

    def ask_save_path(self) -> Optional[str]:
        return self.save_path

    def ask_open_path(self) -> Optional[str]:
        return self.open_path

    def show_message(self, title: str, message: str) -> None:
        self.messages.append((title, message))


class FakeSettingsView(SettingsView):
    def __init__(self) -> None:
        self.field_changed_handler: Optional[Callable[[], None]] = None
        self.highlight_toggled_handler: Optional[Callable[[bool], None]] = None
        self.loaded: Optional[Settings] = None
        self.form_values = Settings()

    def set_on_field_changed(self, handler: Callable[[], None]) -> None:
        self.field_changed_handler = handler

    def set_on_highlight_toggled(self, handler: Callable[[bool], None]) -> None:
        self.highlight_toggled_handler = handler

    def load_settings(self, settings: Settings) -> None:
        self.loaded = settings

    def get_form_values(self) -> Settings:
        return self.form_values


@pytest.fixture
def task_ctx():
    """A full set of task-list-tab Presenter parts (in-memory DB).
    Returns: (model, settings_model, view, presenter).
    """
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)
    try:
        yield model, settings_model, view, presenter
    finally:
        model.close()
        settings_model.close()


@pytest.fixture
def settings_pair():
    """(settings_model, view) for the settings tab. The test itself wires up
    the Presenter, passing on_settings_saved (since it differs per test).
    """
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeSettingsView()
    try:
        yield settings_model, view
    finally:
        settings_model.close()


def test_task_list_presenter_shows_initial_tasks(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx
    assert len(view.shown_tasks) == len(model.list_tasks())


def test_task_list_presenter_edits_cell(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    target = model.list_tasks()[0]
    view.cell_edited_handler(target.id, "assignee", "Suzuki")

    assert model.list_tasks()[0].assignee == "Suzuki"
    # Re-shown to the View after the update
    assert view.shown_tasks[0].assignee == "Suzuki"


def test_task_list_presenter_rejects_empty_name_edit(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    target = model.list_tasks()[0]
    original_name = target.name
    view.cell_edited_handler(target.id, "name", "   ")

    assert model.list_tasks()[0].name == original_name


def test_task_list_presenter_sorts_by_column_and_toggles_direction(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    assert view.sort_state == (None, True)  # Unsorted initially

    view.column_clicked_handler("due_date")
    dates = [t.due_date for t in view.shown_tasks]
    assert dates == sorted(dates)  # Ascending
    assert view.sort_state == ("due_date", True)

    view.column_clicked_handler("due_date")  # Click the same column again -> switches to descending
    dates = [t.due_date for t in view.shown_tasks]
    assert dates == sorted(dates, reverse=True)
    assert view.sort_state == ("due_date", False)

    view.column_clicked_handler("name")  # Click a different column -> starts from ascending
    assert view.sort_state == ("name", True)


def test_task_list_presenter_sorts_priority_by_meaning_not_alphabetically(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    view.column_clicked_handler("priority")

    priorities = [t.priority for t in view.shown_tasks]
    assert priorities == ["Low", "Medium", "Medium", "High", "High"]


def test_task_list_presenter_sort_keeps_blank_values_at_bottom(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    # Mix in one blank task created via "add"
    view.add_handler()
    blank_task = model.list_tasks()[-1]

    # Ascending: blank goes last
    view.column_clicked_handler("assignee")
    assert view.shown_tasks[-1].id == blank_task.id
    assert all(t.assignee.strip() for t in view.shown_tasks[:-1])

    # Descending: blank still stays last (doesn't jump to front)
    view.column_clicked_handler("assignee")
    assert view.sort_state == ("assignee", False)
    assert view.shown_tasks[-1].id == blank_task.id
    assert all(t.assignee.strip() for t in view.shown_tasks[:-1])


def test_task_list_presenter_adds_blank_task_with_default_name(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    before = len(model.list_tasks())
    view.add_handler()

    assert len(model.list_tasks()) == before + 1
    new_task = model.list_tasks()[-1]
    # Placeholder is "highest existing Task N" + 1; none of the seed tasks match, so "Task 1"
    assert new_task.name == "Task 1"
    assert new_task.assignee == ""
    assert new_task.due_date == ""
    assert new_task.priority == ""
    assert new_task.status == ""
    # The row becomes selected after adding
    assert view.selected_task_id == new_task.id


def test_task_list_presenter_add_names_start_at_task_1(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    view.add_handler()
    view.add_handler()

    assert [t.name for t in model.list_tasks()[-2:]] == ["Task 1", "Task 2"]


def test_task_list_presenter_add_always_appears_at_bottom_even_when_sorted(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    # Sort ascending by task name first
    view.column_clicked_handler("name")
    assert view.sort_state == ("name", True)
    sorted_ids_before_add = [t.id for t in view.shown_tasks]

    view.add_handler()
    new_task = model.list_tasks()[-1]

    # Sort arrow disappears, but existing rows keep their sorted order; new task is appended
    assert view.sort_state == (None, True)
    assert [t.id for t in view.shown_tasks] == sorted_ids_before_add + [new_task.id]


def test_task_list_presenter_add_preserves_order_across_further_edits(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    view.column_clicked_handler("due_date")
    order_after_add = [t.id for t in view.shown_tasks]
    view.add_handler()
    new_task = model.list_tasks()[-1]
    order_after_add = order_after_add + [new_task.id]

    # Fixed order survives another edit too (refresh reruns)
    target = model.list_tasks()[0]
    view.cell_edited_handler(target.id, "assignee", "Tanaka")

    assert [t.id for t in view.shown_tasks] == order_after_add


def test_task_list_presenter_two_consecutive_adds_keep_order(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    view.column_clicked_handler("name")
    sorted_ids = [t.id for t in view.shown_tasks]

    view.add_handler()
    first_new = model.list_tasks()[-1]
    view.add_handler()
    second_new = model.list_tasks()[-1]

    # First add's order isn't broken by the second; it's just appended
    assert [t.id for t in view.shown_tasks] == sorted_ids + [first_new.id, second_new.id]


def test_task_list_presenter_add_name_skips_existing_task_number(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    # Rename an existing row to "Task 5" (simulating manual entry or a CSV import)
    seed = model.list_tasks()[0]
    view.cell_edited_handler(seed.id, "name", "Task 5")

    view.add_handler()

    # Max value + 1. Doesn't collide with the existing "Task 5"
    assert model.list_tasks()[-1].name == "Task 6"


def test_task_list_presenter_deletes_task(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    target = model.list_tasks()[0]
    before = len(model.list_tasks())
    view.delete_handler([target.id])

    assert len(model.list_tasks()) == before - 1
    assert all(t.id != target.id for t in model.list_tasks())


def test_task_list_presenter_deletes_multiple_tasks(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    targets = model.list_tasks()[:2]  # Simulating a multi-select
    target_ids = [t.id for t in targets]
    before = len(model.list_tasks())
    view.delete_handler(target_ids)

    assert len(model.list_tasks()) == before - 2
    remaining_ids = {t.id for t in model.list_tasks()}
    assert not remaining_ids & set(target_ids)


def test_task_list_presenter_highlights_overdue_and_warning_tasks(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx
    settings_model.update(Settings(notify_enabled=True, notify_days_before=3))

    today = date.today()
    overdue_task, warning_task, safe_task = model.list_tasks()[:3]

    model.update_task_field(
        overdue_task.id, "due_date", (today - timedelta(days=1)).strftime("%Y-%m-%d")
    )
    model.update_task_field(overdue_task.id, "status", "In Progress")

    model.update_task_field(
        warning_task.id, "due_date", (today + timedelta(days=2)).strftime("%Y-%m-%d")
    )
    model.update_task_field(warning_task.id, "status", "Not Started")

    model.update_task_field(
        safe_task.id, "due_date", (today + timedelta(days=30)).strftime("%Y-%m-%d")
    )
    model.update_task_field(safe_task.id, "status", "Not Started")

    presenter.refresh()

    assert view.highlights.get(overdue_task.id) == "overdue"
    assert view.highlights.get(warning_task.id) == "warning"
    assert safe_task.id not in view.highlights


def test_task_list_presenter_excludes_completed_status_from_highlight(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    task = model.list_tasks()[0]
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    model.update_task_field(task.id, "due_date", yesterday)
    model.update_task_field(task.id, "status", "Done")
    presenter.refresh()

    assert task.id not in view.highlights


def test_task_list_presenter_highlight_follows_due_date_not_status(task_ctx) -> None:
    """No "Overdue" status — red is derived from due_date, so moving it to
    the future clears the red too (never "once red, always red")."""
    model, settings_model, view, presenter = task_ctx

    task = model.list_tasks()[0]
    original_status = task.status
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    view.cell_edited_handler(task.id, "due_date", yesterday)
    assert view.highlights.get(task.id) == "overdue"
    # status is not changed by editing due_date
    assert model.get_task(task.id).status == original_status

    far_future = (date.today() + timedelta(days=60)).strftime("%Y-%m-%d")
    view.cell_edited_handler(task.id, "due_date", far_future)
    assert task.id not in view.highlights


def test_task_list_presenter_disables_highlight_when_notify_off(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx
    settings_model.update(Settings(notify_enabled=False))

    task = model.list_tasks()[0]
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    model.update_task_field(task.id, "due_date", yesterday)
    model.update_task_field(task.id, "status", "In Progress")
    presenter.refresh()

    assert view.highlights == {}


def test_task_list_presenter_export_import_csv(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "tasks.csv")

        view.save_path = path
        view.export_handler()
        assert os.path.exists(path)

        before = len(model.list_tasks())
        view.open_path = path
        view.import_handler()

        assert len(model.list_tasks()) == before * 2
        # One message is shown for the export and one for the import
        assert len(view.messages) == 2


def test_task_list_presenter_export_reports_io_error(task_ctx) -> None:
    """When the export destination can't be opened, show an error message instead of a raw traceback."""
    model, settings_model, view, presenter = task_ctx
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Nonexistent subfolder -> open() raises FileNotFoundError (an OSError)
        view.save_path = os.path.join(tmp_dir, "no_such_dir", "tasks.csv")
        view.export_handler()  # The exception must not leak out

    assert view.messages and view.messages[-1][0] == "Error"


def test_task_list_presenter_import_reports_missing_file(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx
    before = len(model.list_tasks())
    view.open_path = os.path.join(tempfile.gettempdir(), "not_here_20260903.csv")
    view.import_handler()

    assert len(model.list_tasks()) == before  # Nothing is imported
    assert view.messages and view.messages[-1][0] == "Error"


def test_task_list_presenter_import_reports_bad_format(task_ctx) -> None:
    """A CSV without a 'name' column is treated as an error, not "0 imported"."""
    model, settings_model, view, presenter = task_ctx
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "wrong.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write("title,owner\nfoo,bar\n")
        before = len(model.list_tasks())
        view.open_path = path
        view.import_handler()

    assert len(model.list_tasks()) == before
    assert view.messages and view.messages[-1][0] == "Error"


def test_task_list_presenter_import_reports_bad_encoding(task_ctx) -> None:
    """Even a byte sequence that can't be decoded as UTF-8 is shown as an error, not a traceback."""
    model, settings_model, view, presenter = task_ctx
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "bad_encoding.csv")
        with open(path, "wb") as f:
            f.write(b"name,assignee\n\xff\xfe invalid utf-8\n")
        before = len(model.list_tasks())
        view.open_path = path
        view.import_handler()

    assert len(model.list_tasks()) == before
    assert view.messages and view.messages[-1][0] == "Error"


def test_task_list_presenter_auto_saves_on_add(task_ctx) -> None:
    """Every edit (here, an add) is saved immediately — is_dirty() returns False (Auto Save)."""
    model, settings_model, view, presenter = task_ctx

    assert model.is_dirty() is False

    presenter.on_add_click()
    assert model.is_dirty() is False


def test_task_list_presenter_edit_is_immediately_persisted() -> None:
    """An edit is visible from a new TaskModel connection (simulated
    restart), with no explicit Save."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test.db")

        model = TaskModel(db_path=db_path)
        settings_model = SettingsModel(db_path=":memory:")
        view = FakeTaskListView()
        TaskListPresenter(model, settings_model, view)

        target = model.list_tasks()[0]
        view.cell_edited_handler(target.id, "assignee", "Changed")
        assert model.is_dirty() is False

        reopened = TaskModel(db_path=db_path)
        assert reopened.get_task(target.id).assignee == "Changed"

        # Windows can't delete an open file; close connections before leaving TemporaryDirectory
        model.close()
        reopened.close()
        settings_model.close()


def test_backup_and_rotate_copies_current_db_contents() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "app.db")
        model = TaskModel(db_path=db_path)
        model.add_blank_task()
        model.save()
        model.close()

        backup_and_rotate(db_path)

        backup_dir = os.path.join(tmp_dir, "backups")
        backups = os.listdir(backup_dir)
        assert len(backups) == 1

        # Contents at backup time were duplicated (reopen the backup with TaskModel)
        backup_path = os.path.join(backup_dir, backups[0])
        reopened = TaskModel(db_path=backup_path)
        assert len(reopened.list_tasks()) == 6  # 5 demo tasks + 1 added
        reopened.close()


def test_backup_and_rotate_keeps_backups_within_retention_window() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "app.db")
        TaskModel(db_path=db_path).close()  # app.db is created on first construction (seed data inserted)

        for _ in range(5):
            backup_and_rotate(db_path, keep_for=timedelta(hours=24))

        backup_dir = os.path.join(tmp_dir, "backups")
        # All of them were made within the last 24 hours, so all 5 remain
        assert len(os.listdir(backup_dir)) == 5


def test_backup_and_rotate_prunes_backups_older_than_retention_window() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "app.db")
        TaskModel(db_path=db_path).close()

        backup_and_rotate(db_path, keep_for=timedelta(hours=24))
        backup_dir = os.path.join(tmp_dir, "backups")
        old_backup_name = os.listdir(backup_dir)[0]
        old_backup_path = os.path.join(backup_dir, old_backup_name)

        # Pretend this backup was made 25 hours ago (outside the retention window)
        old_time = (datetime.now() - timedelta(hours=25)).timestamp()
        os.utime(old_backup_path, (old_time, old_time))

        # Change the contents, then make one more new backup
        model = TaskModel(db_path=db_path)
        model.add_blank_task()
        model.save()
        model.close()
        backup_and_rotate(db_path, keep_for=timedelta(hours=24))

        backups = os.listdir(backup_dir)
        assert old_backup_name not in backups  # The one outside the retention window is gone
        assert len(backups) == 1  # Only the new one remains


def test_backup_and_rotate_skips_memory_and_missing_files() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # ":memory:" has no file to begin with, so nothing happens
        backup_and_rotate(":memory:")

        # Also does nothing when save() has never been called yet (= the file doesn't exist yet)
        missing_path = os.path.join(tmp_dir, "not_created_yet.db")
        backup_and_rotate(missing_path)

        assert not os.path.exists(os.path.join(tmp_dir, "backups"))


def test_settings_presenter_saves_field_changes_immediately(settings_pair) -> None:
    """Field changes save to the DB immediately, no Save button (Auto Save)."""
    settings_model, view = settings_pair
    SettingsPresenter(settings_model, view, on_settings_saved=lambda: None)

    assert view.loaded == Settings()

    view.form_values = Settings(notify_enabled=False, notify_days_before=7)
    view.field_changed_handler()

    assert settings_model.get().notify_days_before == 7
    assert settings_model.get().notify_enabled is False


def test_settings_default_backup_interval_is_15_minutes() -> None:
    assert Settings().backup_interval_minutes == 15


def test_settings_presenter_saves_backup_interval_immediately(settings_pair) -> None:
    """The backup interval, like other fields, is saved immediately the moment it's changed"""
    settings_model, view = settings_pair
    SettingsPresenter(settings_model, view, on_settings_saved=lambda: None)

    assert settings_model.get().backup_interval_minutes == 15

    view.form_values = Settings(backup_interval_minutes=30)
    view.field_changed_handler()

    assert settings_model.get().backup_interval_minutes == 30


def test_settings_presenter_calls_on_settings_saved_after_field_change(settings_pair) -> None:
    settings_model, view = settings_pair
    saved: List[bool] = []
    SettingsPresenter(settings_model, view, on_settings_saved=lambda: saved.append(True))

    view.field_changed_handler()

    assert len(saved) == 1


def test_settings_presenter_highlight_toggle_applies_immediately(settings_pair) -> None:
    settings_model, view = settings_pair
    saved: List[bool] = []
    SettingsPresenter(settings_model, view, on_settings_saved=lambda: saved.append(True))

    view.highlight_toggled_handler(False)

    assert settings_model.get().notify_enabled is False
    assert len(saved) == 1  # List tab's re-evaluation fires immediately


def test_task_list_presenter_highlight_disappears_immediately_when_toggled_off(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    task = model.list_tasks()[0]
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    model.update_task_field(task.id, "due_date", yesterday)
    model.update_task_field(task.id, "status", "In Progress")
    presenter.refresh()
    assert view.highlights.get(task.id) == "overdue"

    settings_view = FakeSettingsView()
    SettingsPresenter(
        settings_model, settings_view, on_settings_saved=presenter.refresh
    )
    settings_view.highlight_toggled_handler(False)

    assert view.highlights == {}


@pytest.mark.parametrize(
    "existing_names, expected",
    [
        ([], "Task 1"),
        (["Prepare Quotation", "Design Review"], "Task 1"),
        (["Task 1", "Task 2"], "Task 3"),
        (["Task 5"], "Task 6"),
        (["Task 1", "Task 9", "Task 3"], "Task 10"),
        (["Task 007"], "Task 8"),  # Leading zeros are dropped by int()
        # None of these exactly matches "Task <number>", so it falls back to "Task 1"
        (
            ["Task", "Task  3", "task 3", "Task 3x", "My Task 4", "Task -1", "Task ３"],
            "Task 1",
        ),
    ],
)
def test_next_default_task_name(existing_names, expected) -> None:
    assert _next_default_task_name(existing_names) == expected
