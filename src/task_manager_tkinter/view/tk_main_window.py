"""
View (Tkinter implementation layer) — the overall window
--------------------------------------------------------------
Combines the task list tab (TkTaskListFrame) and the settings tab
(TkSettingsFrame) into a ttk.Notebook, and handles launching the whole
window (run). Each tab's own implementation lives under view/task/ and
view/settings/ (one folder per tab).

Edits are always saved to the DB (SQLite) immediately (Auto Save), so there
is no Save button or "unsaved" indicator. Backups against disk corruption
etc. are taken periodically on the main.py side using schedule().
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from task_manager_tkinter.view.settings.tk_frame import TkSettingsFrame
from task_manager_tkinter.view.task.tk_frame import TkTaskListFrame

_WINDOW_WIDTH = 640
_WINDOW_HEIGHT = 560


# Called at main.py > def main()
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
        """Position a window of the given size in the center of the screen.

        Passing only a size to geometry() leaves the initial position up to
        the window manager, which on some environments ends up e.g. in the
        bottom-left. Compute the top-left coordinates from the screen's
        width/height and specify them explicitly in "WxH+X+Y" form.

        On macOS, passing a geometry() with coordinates before the window is
        actually realized gets overwritten by the manager's default position
        on first display. Realize it first with update_idletasks() after
        every widget has been built, then set the coordinates.
        """
        self._root.update_idletasks()
        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()
        x = max((screen_width - width) // 2, 0)
        y = max((screen_height - height) // 2, 0)
        self._root.geometry(f"{width}x{height}+{x}+{y}")

    def schedule(self, delay_ms: int, callback: Callable[[], None]) -> None:
        """Call callback once, delay_ms milliseconds from now (a thin wrapper
        around tkinter's after()).
        To run something repeatedly, have callback itself call schedule()
        again from within (this is how main.py's periodic backup is implemented).
        """
        self._root.after(delay_ms, callback)

    def run(self) -> None:
        self._root.mainloop()

    def destroy(self) -> None:
        """Destroy the window (for tearing down without running run() —
        used by the GUI construction smoke test)."""
        self._root.destroy()
