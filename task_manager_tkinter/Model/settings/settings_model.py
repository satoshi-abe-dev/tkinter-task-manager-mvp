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
    auto_save_enabled: bool = True


class SettingsModel:
    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self._conn = settings_db.connect(db_path)
        notify_enabled, notify_days_before, auto_save_enabled = settings_db.load(self._conn)
        self._settings = Settings(
            notify_enabled=notify_enabled,
            notify_days_before=notify_days_before,
            auto_save_enabled=auto_save_enabled,
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
            settings.auto_save_enabled,
        )
        self._settings = settings

    def set_notify_enabled(self, enabled: bool) -> None:
        """ハイライトの有効/無効だけを即座に切り替える（「保存」を待たずに使う）"""
        self._settings.notify_enabled = enabled
        self._save_current()

    def set_auto_save_enabled(self, enabled: bool) -> None:
        """Auto Saveの有効/無効だけを即座に切り替える（「保存」を待たずに使う）。
        このスイッチ自体は常に即時反映・即時保存される
        （オフのままだと「オンにしたのに保存されていない」という矛盾が起きるため）。
        """
        self._settings.auto_save_enabled = enabled
        self._save_current()

    def _save_current(self) -> None:
        settings_db.save(
            self._conn,
            self._settings.notify_enabled,
            self._settings.notify_days_before,
            self._settings.auto_save_enabled,
        )
