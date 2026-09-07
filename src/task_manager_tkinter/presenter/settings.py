"""
Presenter — 設定タブ
--------------------
設定の読み込み・保存を行う。フィールドが変更されるたびに即座にDBへ保存する
（Auto Save）。CSV書き出し/読み込みはタスクデータに対する操作であり、設定の
概念とは性質が異なるため、タスク一覧タブ側（TaskListPresenter）が担う。
"""

from typing import Callable

from task_manager_tkinter.model.settings import SettingsModel
from task_manager_tkinter.view.settings import SettingsView


class SettingsPresenter:
    def __init__(
        self,
        settings_model: SettingsModel,
        view: SettingsView,
        on_settings_saved: Callable[[], None],
    ) -> None:
        self.settings_model = settings_model
        self.view = view
        self.on_settings_saved = on_settings_saved

        self.view.load_settings(self.settings_model.get())
        self.view.set_on_field_changed(self.on_field_changed)
        self.view.set_on_highlight_toggled(self.on_highlight_toggled)

    def on_field_changed(self) -> None:
        """いずれかの設定項目が変更された時に呼ばれる。即座に保存する"""
        self._save_now()

    def on_highlight_toggled(self, enabled: bool) -> None:
        """ハイライトON/OFFチェックボタンが切り替わった時に呼ばれる。
        一覧タブのハイライト表示へ即座に反映する。
        """
        self.settings_model.set_notify_enabled(enabled)
        self.on_settings_saved()

    def _save_now(self) -> None:
        """Viewのフォームの現在値をそのままDBへ保存する"""
        settings = self.view.get_form_values()
        self.settings_model.update(settings)
        # 通知設定（有効/無効・何日前から）が一覧タブの期限ハイライトに使われて
        # いるため、保存直後に一覧タブへ再評価させる。
        self.on_settings_saved()
