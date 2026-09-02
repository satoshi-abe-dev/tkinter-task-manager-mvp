"""model.settings — アプリ設定のドメイン層。フォルダ ＝ この名前空間。"""

from task_manager_tkinter.model.settings.entity import Settings
from task_manager_tkinter.model.settings.store import SettingsModel

__all__ = ["Settings", "SettingsModel"]
