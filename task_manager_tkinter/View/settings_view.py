"""
View（抽象層）— 設定タブ
------------------------
Presenterが依存する「契約」だけを定義する。
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional

from Model.settings_model import Settings


class SettingsView(ABC):
    @abstractmethod
    def set_on_field_changed(self, handler: Callable[[], None]) -> None:
        """いずれかの設定項目が変更された時に呼ばれるハンドラを登録する（未保存表示に使う）"""

    @abstractmethod
    def set_on_save_click(self, handler: Callable[[], None]) -> None:
        """「変更を保存」ボタン押下時に呼ばれるハンドラを登録する"""

    @abstractmethod
    def set_on_export_click(self, handler: Callable[[], None]) -> None:
        """「書き出し」ボタン押下時に呼ばれるハンドラを登録する"""

    @abstractmethod
    def set_on_import_click(self, handler: Callable[[], None]) -> None:
        """「読み込み」ボタン押下時に呼ばれるハンドラを登録する"""

    @abstractmethod
    def load_settings(self, settings: Settings) -> None:
        """設定値をフォームに反映する（起動時・保存直後などに使う）"""

    @abstractmethod
    def get_form_values(self) -> Settings:
        """フォームの入力値を Settings として返す"""

    @abstractmethod
    def set_dirty(self, dirty: bool) -> None:
        """未保存の変更があるかどうかの表示を切り替える"""

    @abstractmethod
    def ask_save_path(self) -> Optional[str]:
        """書き出し先のファイルパスをユーザーに選ばせる。キャンセル時はNone"""

    @abstractmethod
    def ask_open_path(self) -> Optional[str]:
        """読み込み元のファイルパスをユーザーに選ばせる。キャンセル時はNone"""

    @abstractmethod
    def show_message(self, title: str, message: str) -> None:
        """メッセージをポップアップ表示する"""
