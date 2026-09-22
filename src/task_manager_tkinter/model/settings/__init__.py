"""model.settings — Domain layer for app settings. The folder = this namespace."""

from task_manager_tkinter.model.settings.entity import Settings
from task_manager_tkinter.model.settings.store import SettingsModel

__all__ = ["Settings", "SettingsModel"]
