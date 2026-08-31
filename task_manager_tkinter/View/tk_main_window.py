"""
View（Tkinter実装層）— ウィンドウ全体
--------------------------------------
タスク一覧タブ(TkTaskListFrame)・設定タブ(TkSettingsFrame)をttk.Notebookに
まとめ、ウィンドウ全体の起動(run)を担う。各タブ自体の実装はView/task/、
View/settings/ 以下（タブごとのフォルダ）に分かれている。
"""

import tkinter as tk
from tkinter import ttk

from View.settings.tk_settings_frame import TkSettingsFrame
from View.task.tk_task_list_frame import TkTaskListFrame


# Called at main.py > def main()
class TkMainWindow:
    """2タブ(タスク一覧/設定)をまとめるメインウィンドウ"""

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.title("Task Manager")
        self._root.geometry("640x540")

        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(self._root)
        notebook.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.task_list_frame = TkTaskListFrame(notebook)
        self.settings_frame = TkSettingsFrame(notebook)

        notebook.add(self.task_list_frame, text="Task List")
        notebook.add(self.settings_frame, text="Settings")

    def run(self) -> None:
        self._root.mainloop()
