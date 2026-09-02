"""
Model
-----
アプリ設定の保持のみを行う。永続化は model.lib.settings_db（SQLite）に
委譲しており、SettingsModel自身はSQLの詳細を知らない。
Settings データクラスは model.settings.entity に分離してある。
"""

from task_manager_tkinter.model.lib import settings_db
from task_manager_tkinter.model.lib.db_path import DEFAULT_DB_PATH
from task_manager_tkinter.model.settings.entity import Settings


class SettingsModel:
    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self._conn = settings_db.connect(db_path)
        notify_enabled, notify_days_before, backup_interval_minutes = settings_db.load(
            self._conn
        )
        self._settings = Settings(
            notify_enabled=notify_enabled,
            notify_days_before=notify_days_before,
            backup_interval_minutes=backup_interval_minutes,
        )

    def get(self) -> Settings:
        """現在の設定を返す"""
        return self._settings

    def update(self, settings: Settings) -> None:
        """設定を丸ごと置き換える（DBへも書き込む）"""
        settings_db.save(
            self._conn,
            settings.notify_enabled,
            settings.notify_days_before,
            settings.backup_interval_minutes,
        )
        self._settings = settings

    def set_notify_enabled(self, enabled: bool) -> None:
        """ハイライトの有効/無効だけを即座に切り替える"""
        self._settings.notify_enabled = enabled
        settings_db.save(
            self._conn,
            self._settings.notify_enabled,
            self._settings.notify_days_before,
            self._settings.backup_interval_minutes,
        )
