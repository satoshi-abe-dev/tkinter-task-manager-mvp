"""
view.settings — 設定タブの View 層。フォルダ ＝ この名前空間。

再エクスポートするのは抽象クラス SettingsView（contract.py）だけ（理由は view.task と同じ）。
Tkinter 実装は
`task_manager_tkinter.view.settings.tk_frame` から import すること。
"""

from task_manager_tkinter.view.settings.contract import SettingsView

__all__ = ["SettingsView"]
