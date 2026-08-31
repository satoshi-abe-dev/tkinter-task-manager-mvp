"""
Presenter — 設定タブ
--------------------
設定の読み込み・保存・未保存状態の管理、CSV書き出し/読み込みの橋渡しを行う。
CSV書き出し/読み込みの対象はタスクデータのため、TaskModelにも依存する。
"""

from typing import Callable

from Model.csv_io import export_tasks_to_csv, import_tasks_from_csv
from Model.settings_model import SettingsModel
from Model.task_model import TaskModel
from View.settings_view import SettingsView


class SettingsPresenter:
    def __init__(
        self,
        settings_model: SettingsModel,
        task_model: TaskModel,
        view: SettingsView,
        on_tasks_imported: Callable[[], None],
        on_settings_saved: Callable[[], None],
    ) -> None:
        self.settings_model = settings_model
        self.task_model = task_model
        self.view = view
        self.on_tasks_imported = on_tasks_imported
        self.on_settings_saved = on_settings_saved

        self.view.load_settings(self.settings_model.get())
        self.view.set_dirty(False)
        self.view.set_on_field_changed(self.on_field_changed)
        self.view.set_on_save_click(self.on_save_click)
        self.view.set_on_export_click(self.on_export_click)
        self.view.set_on_import_click(self.on_import_click)

    def on_field_changed(self) -> None:
        self.view.set_dirty(True)

    def on_save_click(self) -> None:
        settings = self.view.get_form_values()
        self.settings_model.update(settings)
        self.view.set_dirty(False)
        # 通知設定（有効/無効・何日前から）が一覧タブの期限ハイライトに使われて
        # いるため、保存直後に一覧タブへ再評価させる。
        self.on_settings_saved()

    def on_export_click(self) -> None:
        path = self.view.ask_save_path()
        if not path:
            return
        export_tasks_to_csv(self.task_model.list_tasks(), path)
        self.view.show_message("お知らせ", f"{path} に書き出しました")

    def on_import_click(self) -> None:
        path = self.view.ask_open_path()
        if not path:
            return
        tasks, skipped = import_tasks_from_csv(path)
        for task in tasks:
            self.task_model.add_task(task)
        self.on_tasks_imported()

        message = f"{len(tasks)}件を読み込みました"
        if skipped:
            message += f"（タスク名が空の{skipped}件はスキップしました）"
        self.view.show_message("お知らせ", message)
