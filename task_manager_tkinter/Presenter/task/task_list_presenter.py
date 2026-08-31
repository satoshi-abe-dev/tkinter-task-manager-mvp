"""
Presenter — タスク一覧タブ
--------------------------
Modelのタスク一覧をViewに反映する橋渡し役。
一覧のインライン編集・カラムヘッダークリックによるソート・期限接近のハイライトを扱う。
"""

from datetime import date, datetime, timedelta
from typing import Callable, Dict, List, Optional

from Model.settings.settings_model import SettingsModel
from Model.task.csv_io import export_tasks_to_csv, import_tasks_from_csv
from Model.task.task import PRIORITIES, STATUSES, Task
from Model.task.task_model import TaskModel
from View.task.task_list_view import TaskListView

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
_EXCLUDED_STATUS = "Done"


class TaskListPresenter:
    def __init__(
        self, model: TaskModel, settings_model: SettingsModel, view: TaskListView
    ) -> None:
        self.model = model
        self.settings_model = settings_model
        self.view = view
        self._sort_field: Optional[str] = None
        self._sort_ascending = True
        # 「追加」直後など、列ソートに従わず「今表示している順番」をそのまま
        # 維持したい時に使う、タスクidの並び順。Noneの間は_sort_fieldに従って
        # 毎回ソートし直す。列ヘッダーをクリックすると解除される。
        self._manual_order: Optional[List[int]] = None
        self.view.set_on_cell_edited(self.on_cell_edited)
        self.view.set_on_column_clicked(self.on_column_clicked)
        self.view.set_on_add_click(self.on_add_click)
        self.view.set_on_delete_click(self.on_delete_click)
        self.view.set_on_export_click(self.on_export_click)
        self.view.set_on_import_click(self.on_import_click)
        self.refresh()

    def refresh(self) -> None:
        """Modelから最新のタスク一覧を取得し、必要ならソートしてViewに反映する。

        設定タブの「Auto Save」がONの場合、この時点で未保存の変更があれば
        即座にsave()する（＝結果として、編集操作のたびに自動保存される）。
        OFFの場合は今まで通り、共通Saveボタンを押すまでDBには反映されない。
        """
        tasks = self._ordered_tasks(self.model.list_tasks())
        self.view.show_tasks(tasks)
        self.view.show_sort_state(self._sort_field, self._sort_ascending)
        self.view.show_due_date_highlights(self._compute_due_date_highlights(tasks))
        if self.settings_model.get().auto_save_enabled and self.model.is_dirty():
            self.model.save()
        self.view.set_dirty(self.model.is_dirty())

    def has_unsaved_changes(self) -> bool:
        """save()していない変更があるかどうか（アプリ終了時の確認ダイアログ用）"""
        return self.model.is_dirty()

    def on_save_click(self) -> None:
        """メモリ上の変更をまとめてDBへ書き込む。Saveボタンはタブの外
        (TkMainWindow側)にあり、main.pyがそこから直接このメソッドを呼ぶ。
        """
        self.model.save()
        self.refresh()

    def _ordered_tasks(self, tasks: List[Task]) -> List[Task]:
        """現在の表示順でタスクを並べる。
        _manual_order（固定順）があればそれを、無ければ現在のソート列の
        結果を使う。「今の並び順」を知りたい場面（追加時など）でも使う
        共通ロジック。
        """
        if self._manual_order is not None:
            return self._apply_manual_order(tasks)
        return self._sorted_tasks(tasks)

    def _sorted_tasks(self, tasks: List[Task]) -> List[Task]:
        """現在のソート列に従ってタスクを並べ替える（列が未指定ならそのまま）。

        値が空欄のタスクは、昇順/降順のどちらでも常に末尾に置く
        （reverse=Trueにすると単純なキー比較だけでは空欄が先頭に来てしまう
        ため、空欄かどうかを別扱いにする必要がある）。
        """
        if self._sort_field is None:
            return tasks
        field = self._sort_field
        key = _SORT_KEYS[field]
        tasks = sorted(tasks, key=key, reverse=not self._sort_ascending)
        # sorted()は安定ソートなので、この後「空欄かどうか」だけで並べ替えれば、
        # 空欄以外の順序(昇順/降順の結果)は保ったまま、空欄だけを末尾に押し出せる。
        tasks = sorted(tasks, key=lambda t: not getattr(t, field).strip())
        return tasks

    def _apply_manual_order(self, tasks: List[Task]) -> List[Task]:
        """_manual_orderで固定した並び順を適用する。

        削除されたタスクのidは自然に取り除かれ、_manual_orderに無い
        新しいid（読み込みなどで増えた分）は末尾に追加する。
        """
        tasks_by_id = {t.id: t for t in tasks}
        ordered_ids = [tid for tid in self._manual_order if tid in tasks_by_id]
        known_ids = set(ordered_ids)
        ordered_ids += [t.id for t in tasks if t.id not in known_ids]
        self._manual_order = ordered_ids
        return [tasks_by_id[tid] for tid in ordered_ids]

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
            if task.status == "Overdue":
                # Statusが手動でOverdueにされている場合は、期限日に関わらず赤にする
                highlights[task.id] = "overdue"
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
        if field == "due_date":
            self._auto_set_overdue_if_past_due(task_id, value)
        self.refresh()

    def _auto_set_overdue_if_past_due(self, task_id: int, due_date_value: str) -> None:
        """期限日を過去の日付に変更した直後、1回だけ自動でStatusをOverdueにする。

        あくまで「編集した瞬間」だけの自動セットであり、継続的に強制する
        わけではない。以降ユーザーが手動でStatusを他の値に変更すれば、
        次に期限日を編集するまではそのまま尊重される（毎回のrefreshで
        Overdueへ戻したりはしない）。Doneのタスクは対象外
        （完了後に期限日を過去へ書き換えても、完了扱いのままにする）。
        """
        try:
            due = datetime.strptime(due_date_value, "%Y-%m-%d").date()
        except ValueError:
            return
        if due >= date.today():
            return
        task = self.model.get_task(task_id)
        if task is None or task.status == _EXCLUDED_STATUS:
            return
        self.model.update_task_field(task_id, "status", "Overdue")

    def on_column_clicked(self, field: str) -> None:
        """一覧タブのカラムヘッダーがクリックされた時に呼ばれる"""
        self._manual_order = None  # 明示的な列ソート操作なので、固定順は解除する
        if self._sort_field == field:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_field = field
            self._sort_ascending = True
        self.refresh()

    def on_add_click(self) -> None:
        """「追加」ボタン押下時に呼ばれる。空欄のタスクを1件追加して選択状態にする。

        今表示されている行の並び順（ソートしていた場合はその結果、既に
        _manual_orderで固定済みならその順番）は変えず、新しいタスクだけを
        末尾に追加する。_sorted_tasks()だけを見ると、2回目以降の追加で
        直前の追加が固定した順番を無視してしまう（_sort_fieldは1回目の
        追加時点で既にNoneになっているため）ので、_manual_orderも考慮する
        _ordered_tasks()を使う。列見出しの矢印は、もう厳密にソートされた
        状態ではないことを示すため非表示にする。
        """
        current_order = [t.id for t in self._ordered_tasks(self.model.list_tasks())]
        task = self.model.add_blank_task()
        self._manual_order = current_order + [task.id]
        self._sort_field = None
        self.refresh()
        self.view.select_task(task.id)

    def on_delete_click(self, task_ids: List[int]) -> None:
        """「削除」ボタン押下時に呼ばれる（確認ポップアップで「はい」が選ばれた後）。
        複数選択している場合は選択中の全件が渡される。
        """
        self.model.delete_tasks(task_ids)
        self.refresh()

    def on_export_click(self) -> None:
        """「書き出し」ボタン押下時に呼ばれる"""
        path = self.view.ask_save_path()
        if not path:
            return
        export_tasks_to_csv(self.model.list_tasks(), path)
        self.view.show_message("Notice", f"Exported to {path}")

    def on_import_click(self) -> None:
        """「読み込み」ボタン押下時に呼ばれる"""
        path = self.view.ask_open_path()
        if not path:
            return
        tasks, skipped = import_tasks_from_csv(path)
        for task in tasks:
            self.model.add_task(task)
        self.refresh()

        message = f"Imported {len(tasks)} task(s)"
        if skipped:
            message += f" ({skipped} skipped due to missing task name)"
        self.view.show_message("Notice", message)
