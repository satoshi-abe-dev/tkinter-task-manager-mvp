"""
Model
-----
アプリ設定の保持のみを行う。永続化はせず、アプリ起動中のみ有効（メモリ上のみ）。
"""

from dataclasses import dataclass


@dataclass
class Settings:
    notify_enabled: bool = True
    notify_days_before: int = 3


class SettingsModel:
    def __init__(self) -> None:
        self._settings = Settings()

    def get(self) -> Settings:
        """現在の設定を返す"""
        return self._settings

    def update(self, settings: Settings) -> None:
        """設定を丸ごと置き換える"""
        self._settings = settings

    def set_notify_enabled(self, enabled: bool) -> None:
        """ハイライトの有効/無効だけを即座に切り替える（「保存」を待たずに使う）"""
        self._settings.notify_enabled = enabled
