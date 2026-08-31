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
    page_size: int = 25
    theme: str = "システムに合わせる"


class SettingsModel:
    def __init__(self) -> None:
        self._settings = Settings()

    def get(self) -> Settings:
        """現在の設定を返す"""
        return self._settings

    def update(self, settings: Settings) -> None:
        """設定を丸ごと置き換える"""
        self._settings = settings
