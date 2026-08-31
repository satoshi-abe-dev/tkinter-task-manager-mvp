"""
Presenter — 設定タブ
--------------------
設定の読み込み・保存・未保存状態の管理を行う。
CSV書き出し/読み込みはタスクデータに対する操作であり、設定の概念とは
性質が異なるため、タスク一覧タブ側（TaskListPresenter）が担う。
"""

from typing import Callable

from Model.settings.settings_model import SettingsModel
from View.settings.settings_view import SettingsView


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
        self.view.set_dirty(False)
        self.view.set_on_field_changed(self.on_field_changed)
        self.view.set_on_highlight_toggled(self.on_highlight_toggled)

    def on_field_changed(self) -> None:
        self.view.set_dirty(True)

    def has_unsaved_changes(self) -> bool:
        """未保存の変更があるかどうか（共通Saveボタンの表示・アプリ終了時の
        確認ダイアログ用）
        """
        return self.view.is_dirty()

    def on_highlight_toggled(self, enabled: bool) -> None:
        """ハイライトON/OFFチェックボタンが切り替わった時に呼ばれる。
        「保存」を待たず、一覧タブのハイライト表示へ即座に反映する。
        """
        self.settings_model.set_notify_enabled(enabled)
        self.on_settings_saved()

    def on_save_click(self) -> None:
        """メモリ上（Viewのフォーム）の変更をまとめてDBへ書き込む。Saveボタンは
        タブの外(TkMainWindow側)にあり、main.pyがそこから直接このメソッドを呼ぶ。
        """
        settings = self.view.get_form_values()
        self.settings_model.update(settings)
        self.view.set_dirty(False)
        # 通知設定（有効/無効・何日前から）が一覧タブの期限ハイライトに使われて
        # いるため、保存直後に一覧タブへ再評価させる。
        self.on_settings_saved()
