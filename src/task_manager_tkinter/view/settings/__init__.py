"""
view.settings — View layer for the settings tab. The folder = this namespace.

Only re-exports the abstract SettingsView (contract.py) — same reason as
view.task. Import the Tkinter implementation from
`task_manager_tkinter.view.settings.tk_frame` directly.
"""

from task_manager_tkinter.view.settings.contract import SettingsView

__all__ = ["SettingsView"]
