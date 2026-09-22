"""
Model
-----
Holds the app settings only. Persistence is delegated to model.lib.settings_db
(SQLite); SettingsModel itself knows nothing about the SQL details.
The Settings dataclass is kept separate, in model.settings.entity.
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

    def close(self) -> None:
        """Close the DB connection (same reason as TaskModel.close() — mainly for tests)."""
        self._conn.close()

    def get(self) -> Settings:
        """Return the current settings"""
        return self._settings

    def update(self, settings: Settings) -> None:
        """Replace the settings wholesale (also writes to the DB)"""
        settings_db.save(
            self._conn,
            settings.notify_enabled,
            settings.notify_days_before,
            settings.backup_interval_minutes,
        )
        self._settings = settings

    def set_notify_enabled(self, enabled: bool) -> None:
        """Toggle just the highlight enabled/disabled flag, immediately"""
        self._settings.notify_enabled = enabled
        settings_db.save(
            self._conn,
            self._settings.notify_enabled,
            self._settings.notify_days_before,
            self._settings.backup_interval_minutes,
        )
