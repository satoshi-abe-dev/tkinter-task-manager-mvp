"""
Model
-----
アプリ設定の保持のみを行う。永続化はModel.settings.settings_db（SQLite）に
委譲しており、SettingsModel自身はSQLの詳細を知らない。
"""

from dataclasses import dataclass

from Model.db_path import DEFAULT_DB_PATH
from Model.settings import settings_db


@dataclass
class Settings:
    notify_enabled: bool = True
    notify_days_before: int = 3


class SettingsModel:
    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self._conn = settings_db.connect(db_path)
        notify_enabled, notify_days_before = settings_db.load(self._conn)
        self._settings = Settings(
            notify_enabled=notify_enabled, notify_days_before=notify_days_before
        )

    def get(self) -> Settings:
        """現在の設定を返す"""
        return self._settings

    def update(self, settings: Settings) -> None:
        """設定を丸ごと置き換える（DBへも書き込む）"""
        settings_db.save(self._conn, settings.notify_enabled, settings.notify_days_before)
        self._settings = settings

    def set_notify_enabled(self, enabled: bool) -> None:
        """ハイライトの有効/無効だけを即座に切り替える"""
        self._settings.notify_enabled = enabled
        settings_db.save(
            self._conn, self._settings.notify_enabled, self._settings.notify_days_before
        )
