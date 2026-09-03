"""
Presenter の単体テスト（pytest）
--------------------------------
FakeView（各 View 抽象クラスの偽実装）を差し込むことで、Tkinter を一切起動せずに
2 つの Presenter のロジックを検証する。View 以下の Tkinter 実装
（view/task/tk_frame.py / view/settings/tk_frame.py / view/tk_main_window.py）は
読み込まないため、tkinter が入っていない環境でも実行できる。

実行方法（リポジトリのルートで）:
    pip install -r requirements-dev.txt
    pytest
"""

import os
import tempfile
from datetime import date, datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple

import pytest

from task_manager_tkinter.model.lib.db_backup import backup_and_rotate
from task_manager_tkinter.model.settings import Settings, SettingsModel
from task_manager_tkinter.model.task import Task, TaskModel
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
    """タスク一覧タブの Presenter 一式（インメモリ DB）。
    戻り値: (model, settings_model, view, presenter)。
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
    """設定タブ用の (settings_model, view)。Presenter はテスト側で
    on_settings_saved を渡して組む（テストごとに中身が違うため）。
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
    # 更新後にViewへ再表示されている
    assert view.shown_tasks[0].assignee == "Suzuki"


def test_task_list_presenter_rejects_empty_name_edit(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    target = model.list_tasks()[0]
    original_name = target.name
    view.cell_edited_handler(target.id, "name", "   ")

    assert model.list_tasks()[0].name == original_name


def test_task_list_presenter_sorts_by_column_and_toggles_direction(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

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


def test_task_list_presenter_sorts_priority_by_meaning_not_alphabetically(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    view.column_clicked_handler("priority")

    priorities = [t.priority for t in view.shown_tasks]
    assert priorities == ["Low", "Medium", "Medium", "High", "High"]


def test_task_list_presenter_sort_keeps_blank_values_at_bottom(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

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


def test_task_list_presenter_adds_blank_task_with_id_based_name(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

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


def test_task_list_presenter_add_always_appears_at_bottom_even_when_sorted(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

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


def test_task_list_presenter_add_preserves_order_across_further_edits(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    view.column_clicked_handler("due_date")
    order_after_add = [t.id for t in view.shown_tasks]
    view.add_handler()
    new_task = model.list_tasks()[-1]
    order_after_add = order_after_add + [new_task.id]

    # 追加後に別のセルを編集しても(=refreshが再度走っても)、固定した順番は保たれる
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

    # 1回目の追加が固定した並び順を、2回目の追加でも壊さず、末尾に足すだけ
    assert [t.id for t in view.shown_tasks] == sorted_ids + [first_new.id, second_new.id]


def test_task_list_presenter_add_name_survives_deletion_without_duplicate(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    view.add_handler()
    first_new = model.list_tasks()[-1]
    view.delete_handler([first_new.id])
    view.add_handler()
    second_new = model.list_tasks()[-1]

    # 同じ名前(id基準)が使い回されず、常に一意になる
    assert first_new.name != second_new.name


def test_task_list_presenter_deletes_task(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    target = model.list_tasks()[0]
    before = len(model.list_tasks())
    view.delete_handler([target.id])

    assert len(model.list_tasks()) == before - 1
    assert all(t.id != target.id for t in model.list_tasks())


def test_task_list_presenter_deletes_multiple_tasks(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx

    targets = model.list_tasks()[:2]  # 複数選択のシミュレーション
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
    """「Overdue」という状態は無い。期限切れの赤は due_date からのみ決まり、
    期限を未来に直せば赤も消える（＝一度赤くなったら戻らない、が起きない）。
    """
    model, settings_model, view, presenter = task_ctx

    task = model.list_tasks()[0]
    original_status = task.status
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    view.cell_edited_handler(task.id, "due_date", yesterday)
    assert view.highlights.get(task.id) == "overdue"
    # status は due_date 編集では書き換わらない
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
        # 書き出し・読み込みそれぞれで1件ずつメッセージが表示される
        assert len(view.messages) == 2


def test_task_list_presenter_export_reports_io_error(task_ctx) -> None:
    """書き出し先が開けない時、素のトレースバックではなくエラーメッセージを出す。"""
    model, settings_model, view, presenter = task_ctx
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 存在しないサブフォルダの下 → open() が FileNotFoundError(OSError)
        view.save_path = os.path.join(tmp_dir, "no_such_dir", "tasks.csv")
        view.export_handler()  # 例外が外に漏れないこと

    assert view.messages and view.messages[-1][0] == "Error"


def test_task_list_presenter_import_reports_missing_file(task_ctx) -> None:
    model, settings_model, view, presenter = task_ctx
    before = len(model.list_tasks())
    view.open_path = os.path.join(tempfile.gettempdir(), "not_here_20260903.csv")
    view.import_handler()

    assert len(model.list_tasks()) == before  # 何も取り込まれない
    assert view.messages and view.messages[-1][0] == "Error"


def test_task_list_presenter_import_reports_bad_format(task_ctx) -> None:
    """'name' 列が無い CSV は「0件取り込み」ではなくエラーにする。"""
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
    """UTF-8 として解釈できないバイト列でも、トレースバックにせずエラー表示。"""
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
    """編集操作(ここでは追加)のたびに即座に保存され、model.is_dirty()が
    Falseに戻る(Auto Save)。
    """
    model, settings_model, view, presenter = task_ctx

    assert model.is_dirty() is False

    presenter.on_add_click()
    assert model.is_dirty() is False


def test_task_list_presenter_edit_is_immediately_persisted() -> None:
    """セル編集した内容が、別の接続(=再起動を模した新しいTaskModel)からも
    即座に見えることを確認する(Save操作を挟まない)。
    """
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

        # Windowsは開いているファイルを削除できないので、TemporaryDirectoryを
        # 抜ける前に接続を閉じる。
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

        # バックアップ時点の内容が複製されていることを確認する
        # (バックアップされたファイルをそのままTaskModelで開いて中身を見る)
        backup_path = os.path.join(backup_dir, backups[0])
        reopened = TaskModel(db_path=backup_path)
        assert len(reopened.list_tasks()) == 6  # デモ5件 + 追加した1件
        reopened.close()


def test_backup_and_rotate_keeps_backups_within_retention_window() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "app.db")
        TaskModel(db_path=db_path).close()  # 初回作成(シード投入)でapp.dbができる

        for _ in range(5):
            backup_and_rotate(db_path, keep_for=timedelta(hours=24))

        backup_dir = os.path.join(tmp_dir, "backups")
        # 全部24時間以内に作られたものなので、5件とも残る
        assert len(os.listdir(backup_dir)) == 5


def test_backup_and_rotate_prunes_backups_older_than_retention_window() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "app.db")
        TaskModel(db_path=db_path).close()

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
        model.close()
        backup_and_rotate(db_path, keep_for=timedelta(hours=24))

        backups = os.listdir(backup_dir)
        assert old_backup_name not in backups  # 保持期間外のものは消えている
        assert len(backups) == 1  # 新しいものだけ残っている


def test_backup_and_rotate_skips_memory_and_missing_files() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # :memory: はそもそもファイルが無いので何もしない
        backup_and_rotate(":memory:")

        # まだ一度もsave()していない(=ファイルがまだ無い)場合も何もしない
        missing_path = os.path.join(tmp_dir, "not_created_yet.db")
        backup_and_rotate(missing_path)

        assert not os.path.exists(os.path.join(tmp_dir, "backups"))


def test_settings_presenter_saves_field_changes_immediately(settings_pair) -> None:
    """フィールドを変更した瞬間に、Saveボタンを介さず即座にDBへ保存される
    （Auto Save）。
    """
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
    """バックアップ間隔も、他のフィールドと同様に変更した瞬間に即座に保存される"""
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
    assert len(saved) == 1  # 一覧タブの再評価(ハイライトOFF反映)が即座に呼ばれる


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
