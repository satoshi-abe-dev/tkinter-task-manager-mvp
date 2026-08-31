"""
Presenterの単体テスト例
-----------------------
FakeView（各View抽象クラスの偽実装）を差し込むことで、Tkinterを一切起動せずに
2つのPresenterのロジックを検証する。View以下のTkinter実装（tk_task_list_frame.py /
tk_settings_frame.py / tk_main_window.py）は読み込まないため、tkinterが
インストールされていない環境でもこのテストは実行できる。

実行方法:
    このフォルダ(task_manager_tkinter)の直下で
        python3 test_presenter.py
"""

import os
import tempfile
from datetime import date, datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple

from Model.db_backup import backup_and_rotate
from Model.settings.settings_model import Settings, SettingsModel
from Model.task.task import Task
from Model.task.task_model import TaskModel
from Presenter.settings.settings_presenter import SettingsPresenter
from Presenter.task.task_list_presenter import TaskListPresenter
from View.settings.settings_view import SettingsView
from View.task.task_list_view import TaskListView


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


def test_task_list_presenter_shows_initial_tasks() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    TaskListPresenter(model, settings_model, view)

    assert len(view.shown_tasks) == len(model.list_tasks())
    print("test_task_list_presenter_shows_initial_tasks: OK")


def test_task_list_presenter_edits_cell() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    target = model.list_tasks()[0]
    view.cell_edited_handler(target.id, "assignee", "Suzuki")

    assert model.list_tasks()[0].assignee == "Suzuki"
    # 更新後にViewへ再表示されている
    assert view.shown_tasks[0].assignee == "Suzuki"
    print("test_task_list_presenter_edits_cell: OK")


def test_task_list_presenter_rejects_empty_name_edit() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    target = model.list_tasks()[0]
    original_name = target.name
    view.cell_edited_handler(target.id, "name", "   ")

    assert model.list_tasks()[0].name == original_name
    print("test_task_list_presenter_rejects_empty_name_edit: OK")


def test_task_list_presenter_sorts_by_column_and_toggles_direction() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

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
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    view.column_clicked_handler("priority")

    priorities = [t.priority for t in view.shown_tasks]
    assert priorities == ["Low", "Medium", "Medium", "High", "High"]
    print("test_task_list_presenter_sorts_priority_by_meaning_not_alphabetically: OK")


def test_task_list_presenter_sort_keeps_blank_values_at_bottom() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    # 「追加」で作った空欄タスクを1件混ぜる
    view.add_handler()
    blank_task = model.list_tasks()[-1]

    # 昇順: 空欄は末尾
    view.column_clicked_handler("assignee")
    assert view.shown_tasks[-1].id == blank_task.id
    assert all(t.assignee.strip() for t in view.shown_tasks[:-1])

    # 降順に切り替えても、空欄は引き続き末尾（先頭に来てはいけない）
    view.column_clicked_handler("assignee")
    assert view.sort_state == ("assignee", False)
    assert view.shown_tasks[-1].id == blank_task.id
    assert all(t.assignee.strip() for t in view.shown_tasks[:-1])
    print("test_task_list_presenter_sort_keeps_blank_values_at_bottom: OK")


def test_task_list_presenter_adds_blank_task_with_id_based_name() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    before = len(model.list_tasks())
    view.add_handler()

    assert len(model.list_tasks()) == before + 1
    new_task = model.list_tasks()[-1]
    # タスク名は件数ベースではなく、id基準の連番（削除後に追加しても重複しない）
    assert new_task.name == f"Task {new_task.id}"
    assert new_task.assignee == ""
    assert new_task.due_date == ""
    assert new_task.priority == ""
    assert new_task.status == ""
    # 追加後、その行が選択状態になる
    assert view.selected_task_id == new_task.id
    print("test_task_list_presenter_adds_blank_task_with_id_based_name: OK")


def test_task_list_presenter_add_always_appears_at_bottom_even_when_sorted() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    # タスク名で昇順ソートしておく
    view.column_clicked_handler("name")
    assert view.sort_state == ("name", True)
    sorted_ids_before_add = [t.id for t in view.shown_tasks]

    view.add_handler()
    new_task = model.list_tasks()[-1]

    # 見出しの矢印(ソート中の目印)は消えるが、
    assert view.sort_state == (None, True)
    # 既存の行の並び順はソートしていた時のまま変わらず、新タスクだけが末尾に足される
    assert [t.id for t in view.shown_tasks] == sorted_ids_before_add + [new_task.id]
    print("test_task_list_presenter_add_always_appears_at_bottom_even_when_sorted: OK")


def test_task_list_presenter_add_preserves_order_across_further_edits() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    view.column_clicked_handler("due_date")
    order_after_add = [t.id for t in view.shown_tasks]
    view.add_handler()
    new_task = model.list_tasks()[-1]
    order_after_add = order_after_add + [new_task.id]

    # 追加後に別のセルを編集しても(=refreshが再度走っても)、固定した順番は保たれる
    target = model.list_tasks()[0]
    view.cell_edited_handler(target.id, "assignee", "Tanaka")

    assert [t.id for t in view.shown_tasks] == order_after_add
    print("test_task_list_presenter_add_preserves_order_across_further_edits: OK")


def test_task_list_presenter_two_consecutive_adds_keep_order() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    view.column_clicked_handler("name")
    sorted_ids = [t.id for t in view.shown_tasks]

    view.add_handler()
    first_new = model.list_tasks()[-1]
    view.add_handler()
    second_new = model.list_tasks()[-1]

    # 1回目の追加が固定した並び順を、2回目の追加でも壊さず、末尾に足すだけ
    assert [t.id for t in view.shown_tasks] == sorted_ids + [first_new.id, second_new.id]
    print("test_task_list_presenter_two_consecutive_adds_keep_order: OK")


def test_task_list_presenter_add_name_survives_deletion_without_duplicate() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    view.add_handler()
    first_new = model.list_tasks()[-1]
    view.delete_handler([first_new.id])
    view.add_handler()
    second_new = model.list_tasks()[-1]

    # 同じ名前(id基準)が使い回されず、常に一意になる
    assert first_new.name != second_new.name
    print("test_task_list_presenter_add_name_survives_deletion_without_duplicate: OK")


def test_task_list_presenter_deletes_task() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    target = model.list_tasks()[0]
    before = len(model.list_tasks())
    view.delete_handler([target.id])

    assert len(model.list_tasks()) == before - 1
    assert all(t.id != target.id for t in model.list_tasks())
    print("test_task_list_presenter_deletes_task: OK")


def test_task_list_presenter_deletes_multiple_tasks() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    targets = model.list_tasks()[:2]  # 複数選択のシミュレーション
    target_ids = [t.id for t in targets]
    before = len(model.list_tasks())
    view.delete_handler(target_ids)

    assert len(model.list_tasks()) == before - 2
    remaining_ids = {t.id for t in model.list_tasks()}
    assert not remaining_ids & set(target_ids)
    print("test_task_list_presenter_deletes_multiple_tasks: OK")


def test_task_list_presenter_highlights_overdue_and_warning_tasks() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    settings_model.update(Settings(notify_enabled=True, notify_days_before=3))
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

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
    print("test_task_list_presenter_highlights_overdue_and_warning_tasks: OK")


def test_task_list_presenter_excludes_completed_status_from_highlight() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    task = model.list_tasks()[0]
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    model.update_task_field(task.id, "due_date", yesterday)
    model.update_task_field(task.id, "status", "Done")
    presenter.refresh()

    assert task.id not in view.highlights
    print("test_task_list_presenter_excludes_completed_status_from_highlight: OK")


def test_task_list_presenter_highlights_manually_set_overdue_status() -> None:
    """Statusを手動でOverdueにしたタスクは、期限日が未来でも赤くなる"""
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    task = model.list_tasks()[0]
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    model.update_task_field(task.id, "due_date", tomorrow)
    model.update_task_field(task.id, "status", "Overdue")
    presenter.refresh()

    assert view.highlights.get(task.id) == "overdue"
    print("test_task_list_presenter_highlights_manually_set_overdue_status: OK")


def test_task_list_presenter_auto_sets_overdue_status_on_past_due_date_edit() -> None:
    """期限日を過去の日付にインライン編集した瞬間、自動でStatusがOverdueになる"""
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    task = model.list_tasks()[0]
    model.update_task_field(task.id, "status", "In Progress")
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    view.cell_edited_handler(task.id, "due_date", yesterday)

    assert model.get_task(task.id).status == "Overdue"
    print("test_task_list_presenter_auto_sets_overdue_status_on_past_due_date_edit: OK")


def test_task_list_presenter_auto_overdue_excludes_done_status() -> None:
    """Doneのタスクは、期限日を過去にしてもStatusをOverdueに自動変更しない"""
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    task = model.list_tasks()[0]
    model.update_task_field(task.id, "status", "Done")
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    view.cell_edited_handler(task.id, "due_date", yesterday)

    assert model.get_task(task.id).status == "Done"
    print("test_task_list_presenter_auto_overdue_excludes_done_status: OK")


def test_task_list_presenter_auto_overdue_is_one_time_only() -> None:
    """自動Overdueは編集した瞬間だけの一度きりで、その後の手動変更は上書きしない"""
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    task = model.list_tasks()[0]
    model.update_task_field(task.id, "status", "In Progress")
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    view.cell_edited_handler(task.id, "due_date", yesterday)
    assert model.get_task(task.id).status == "Overdue"

    # ユーザーが手動で"In Progress"に戻す（期限日はそのまま過去日）
    view.cell_edited_handler(task.id, "status", "In Progress")
    # 別のセルを編集してrefreshが走っても、Overdueへ勝手に戻されない
    view.cell_edited_handler(task.id, "assignee", "Suzuki")

    assert model.get_task(task.id).status == "In Progress"
    print("test_task_list_presenter_auto_overdue_is_one_time_only: OK")


def test_task_list_presenter_disables_highlight_when_notify_off() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    settings_model.update(Settings(notify_enabled=False))
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    task = model.list_tasks()[0]
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    model.update_task_field(task.id, "due_date", yesterday)
    model.update_task_field(task.id, "status", "In Progress")
    presenter.refresh()

    assert view.highlights == {}
    print("test_task_list_presenter_disables_highlight_when_notify_off: OK")


def test_task_list_presenter_export_import_csv() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "tasks.csv")

        view.save_path = path
        view.export_handler()
        assert os.path.exists(path)

        before = len(model.list_tasks())
        view.open_path = path
        view.import_handler()

        assert len(model.list_tasks()) == before * 2
        # 書き出し・読み込みそれぞれで1件ずつメッセージが表示される
        assert len(view.messages) == 2
    print("test_task_list_presenter_export_import_csv: OK")


def test_task_list_presenter_auto_saves_on_add() -> None:
    """編集操作(ここでは追加)のたびに即座に保存され、model.is_dirty()が
    Falseに戻る(Auto Save)。
    """
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeTaskListView()
    presenter = TaskListPresenter(model, settings_model, view)

    assert model.is_dirty() is False

    presenter.on_add_click()
    assert model.is_dirty() is False
    print("test_task_list_presenter_auto_saves_on_add: OK")


def test_task_list_presenter_edit_is_immediately_persisted() -> None:
    """セル編集した内容が、別の接続(=再起動を模した新しいTaskModel)からも
    即座に見えることを確認する(Save操作を挟まない)。
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test.db")

        model = TaskModel(db_path=db_path)
        settings_model = SettingsModel(db_path=":memory:")
        view = FakeTaskListView()
        presenter = TaskListPresenter(model, settings_model, view)

        target = model.list_tasks()[0]
        view.cell_edited_handler(target.id, "assignee", "Changed")
        assert model.is_dirty() is False

        reopened = TaskModel(db_path=db_path)
        assert reopened.get_task(target.id).assignee == "Changed"

    print("test_task_list_presenter_edit_is_immediately_persisted: OK")


def test_backup_and_rotate_copies_current_db_contents() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "app.db")
        model = TaskModel(db_path=db_path)
        model.add_blank_task()
        model.save()

        backup_and_rotate(db_path)

        backup_dir = os.path.join(tmp_dir, "backups")
        backups = os.listdir(backup_dir)
        assert len(backups) == 1

        # バックアップ時点の内容が複製されていることを確認する
        # (バックアップされたファイルをそのままTaskModelで開いて中身を見る)
        backup_path = os.path.join(backup_dir, backups[0])
        reopened = TaskModel(db_path=backup_path)
        assert len(reopened.list_tasks()) == 6  # デモ5件 + 追加した1件
    print("test_backup_and_rotate_copies_current_db_contents: OK")


def test_backup_and_rotate_keeps_backups_within_retention_window() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "app.db")
        TaskModel(db_path=db_path)  # 初回作成(シード投入・自動保存)でapp.dbができる

        for _ in range(5):
            backup_and_rotate(db_path, keep_for=timedelta(hours=24))

        backup_dir = os.path.join(tmp_dir, "backups")
        # 全部24時間以内に作られたものなので、5件とも残る
        assert len(os.listdir(backup_dir)) == 5
    print("test_backup_and_rotate_keeps_backups_within_retention_window: OK")


def test_backup_and_rotate_prunes_backups_older_than_retention_window() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "app.db")
        TaskModel(db_path=db_path)

        backup_and_rotate(db_path, keep_for=timedelta(hours=24))
        backup_dir = os.path.join(tmp_dir, "backups")
        old_backup_name = os.listdir(backup_dir)[0]
        old_backup_path = os.path.join(backup_dir, old_backup_name)

        # このバックアップを25時間前に作られたことにする(保持期間の外)
        old_time = (datetime.now() - timedelta(hours=25)).timestamp()
        os.utime(old_backup_path, (old_time, old_time))

        # 内容を変えてから、新しいバックアップをもう1つ作る
        model = TaskModel(db_path=db_path)
        model.add_blank_task()
        model.save()
        backup_and_rotate(db_path, keep_for=timedelta(hours=24))

        backups = os.listdir(backup_dir)
        assert old_backup_name not in backups  # 保持期間外のものは消えている
        assert len(backups) == 1  # 新しいものだけ残っている
    print("test_backup_and_rotate_prunes_backups_older_than_retention_window: OK")


def test_backup_and_rotate_skips_memory_and_missing_files() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # :memory: はそもそもファイルが無いので何もしない
        backup_and_rotate(":memory:")

        # まだ一度もsave()していない(=ファイルがまだ無い)場合も何もしない
        missing_path = os.path.join(tmp_dir, "not_created_yet.db")
        backup_and_rotate(missing_path)

        assert not os.path.exists(os.path.join(tmp_dir, "backups"))
    print("test_backup_and_rotate_skips_memory_and_missing_files: OK")


def test_settings_presenter_saves_field_changes_immediately() -> None:
    """フィールドを変更した瞬間に、Saveボタンを介さず即座にDBへ保存される
    （Auto Save）。
    """
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeSettingsView()
    SettingsPresenter(settings_model, view, on_settings_saved=lambda: None)

    assert view.loaded == Settings()

    view.form_values = Settings(notify_enabled=False, notify_days_before=7)
    view.field_changed_handler()

    assert settings_model.get().notify_days_before == 7
    assert settings_model.get().notify_enabled is False
    print("test_settings_presenter_saves_field_changes_immediately: OK")


def test_settings_default_backup_interval_is_15_minutes() -> None:
    assert Settings().backup_interval_minutes == 15
    print("test_settings_default_backup_interval_is_15_minutes: OK")


def test_settings_presenter_saves_backup_interval_immediately() -> None:
    """バックアップ間隔も、他のフィールドと同様に変更した瞬間に即座に保存される"""
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeSettingsView()
    SettingsPresenter(settings_model, view, on_settings_saved=lambda: None)

    assert settings_model.get().backup_interval_minutes == 15

    view.form_values = Settings(backup_interval_minutes=30)
    view.field_changed_handler()

    assert settings_model.get().backup_interval_minutes == 30
    print("test_settings_presenter_saves_backup_interval_immediately: OK")


def test_settings_presenter_calls_on_settings_saved_after_field_change() -> None:
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeSettingsView()
    saved: List[bool] = []
    SettingsPresenter(settings_model, view, on_settings_saved=lambda: saved.append(True))

    view.field_changed_handler()

    assert len(saved) == 1
    print("test_settings_presenter_calls_on_settings_saved_after_field_change: OK")


def test_settings_presenter_highlight_toggle_applies_immediately() -> None:
    settings_model = SettingsModel(db_path=":memory:")
    view = FakeSettingsView()
    saved: List[bool] = []
    SettingsPresenter(settings_model, view, on_settings_saved=lambda: saved.append(True))

    view.highlight_toggled_handler(False)

    assert settings_model.get().notify_enabled is False
    assert len(saved) == 1  # 一覧タブの再評価(ハイライトOFF反映)が即座に呼ばれる
    print("test_settings_presenter_highlight_toggle_applies_immediately: OK")


def test_task_list_presenter_highlight_disappears_immediately_when_toggled_off() -> None:
    model = TaskModel(db_path=":memory:")
    settings_model = SettingsModel(db_path=":memory:")
    task_view = FakeTaskListView()
    task_presenter = TaskListPresenter(model, settings_model, task_view)

    task = model.list_tasks()[0]
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    model.update_task_field(task.id, "due_date", yesterday)
    model.update_task_field(task.id, "status", "In Progress")
    task_presenter.refresh()
    assert task_view.highlights.get(task.id) == "overdue"

    settings_view = FakeSettingsView()
    SettingsPresenter(
        settings_model, settings_view, on_settings_saved=task_presenter.refresh
    )
    settings_view.highlight_toggled_handler(False)

    assert task_view.highlights == {}
    print("test_task_list_presenter_highlight_disappears_immediately_when_toggled_off: OK")


if __name__ == "__main__":
    test_task_list_presenter_shows_initial_tasks()
    test_task_list_presenter_edits_cell()
    test_task_list_presenter_rejects_empty_name_edit()
    test_task_list_presenter_sorts_by_column_and_toggles_direction()
    test_task_list_presenter_sorts_priority_by_meaning_not_alphabetically()
    test_task_list_presenter_sort_keeps_blank_values_at_bottom()
    test_task_list_presenter_adds_blank_task_with_id_based_name()
    test_task_list_presenter_add_always_appears_at_bottom_even_when_sorted()
    test_task_list_presenter_add_preserves_order_across_further_edits()
    test_task_list_presenter_two_consecutive_adds_keep_order()
    test_task_list_presenter_add_name_survives_deletion_without_duplicate()
    test_task_list_presenter_deletes_task()
    test_task_list_presenter_deletes_multiple_tasks()
    test_task_list_presenter_highlights_overdue_and_warning_tasks()
    test_task_list_presenter_excludes_completed_status_from_highlight()
    test_task_list_presenter_highlights_manually_set_overdue_status()
    test_task_list_presenter_auto_sets_overdue_status_on_past_due_date_edit()
    test_task_list_presenter_auto_overdue_excludes_done_status()
    test_task_list_presenter_auto_overdue_is_one_time_only()
    test_task_list_presenter_disables_highlight_when_notify_off()
    test_task_list_presenter_export_import_csv()
    test_task_list_presenter_auto_saves_on_add()
    test_task_list_presenter_edit_is_immediately_persisted()
    test_backup_and_rotate_copies_current_db_contents()
    test_backup_and_rotate_keeps_backups_within_retention_window()
    test_backup_and_rotate_prunes_backups_older_than_retention_window()
    test_backup_and_rotate_skips_memory_and_missing_files()
    test_settings_presenter_saves_field_changes_immediately()
    test_settings_default_backup_interval_is_15_minutes()
    test_settings_presenter_saves_backup_interval_immediately()
    test_settings_presenter_calls_on_settings_saved_after_field_change()
    test_settings_presenter_highlight_toggle_applies_immediately()
    test_task_list_presenter_highlight_disappears_immediately_when_toggled_off()
