"""
View (Tkinter implementation layer) — the overall window
--------------------------------------------------------------
Combines the task list tab (TkTaskListFrame) and the settings tab
(TkSettingsFrame) into a ttk.Notebook, and handles launching the window
(run). Each tab's own implementation lives under view/task/ and
view/settings/.

Auto Save means no Save button or "unsaved" indicator. Backups run
periodically from main.py via schedule().
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from task_manager_tkinter.view.settings.tk_frame import TkSettingsFrame
from task_manager_tkinter.view.task.tk_frame import TkTaskListFrame

_WINDOW_WIDTH = 640
_WINDOW_HEIGHT = 560


class TkMainWindow:
    """The main window combining the two tabs (task list / settings)"""

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.title("Task Manager")
        self._root.geometry(f"{_WINDOW_WIDTH}x{_WINDOW_HEIGHT}")

        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(self._root)
        notebook.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.task_list_frame = TkTaskListFrame(notebook)
        self.settings_frame = TkSettingsFrame(notebook)

        notebook.add(self.task_list_frame, text="Task List")
        notebook.add(self.settings_frame, text="Settings")

        self._center_on_screen(_WINDOW_WIDTH, _WINDOW_HEIGHT)

    def _center_on_screen(self, width: int, height: int) -> None:
        """Center a window of the given size on the screen.

        geometry() with size alone leaves position to the window manager
        (can land bottom-left), so compute top-left coords explicitly as
        "WxH+X+Y". On macOS, setting coords before the window is realized
        gets overwritten by the manager's default — call update_idletasks()
        first.
        """
        self._root.update_idletasks()
        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()
        x = max((screen_width - width) // 2, 0)
        y = max((screen_height - height) // 2, 0)
        self._root.geometry(f"{width}x{height}+{x}+{y}")

    def schedule(self, delay_ms: int, callback: Callable[[], None]) -> None:
        """Call callback once, delay_ms ms from now (wraps tkinter's after()).
        For repeats, have callback call schedule() again itself — see
        main.py's periodic backup."""
        self._root.after(delay_ms, callback)

    def run(self) -> None:
        self._root.mainloop()

    def destroy(self) -> None:
        """Destroy the window without running run() (used by the GUI smoke test)"""
        self._root.destroy()
