"""
View（Tkinter実装層）— ウィンドウ全体
--------------------------------------
タスク一覧タブ(TkTaskListFrame)・設定タブ(TkSettingsFrame)をttk.Notebookに
まとめ、ウィンドウ全体の起動(run)を担う。各タブ自体の実装は view/task/、
view/settings/ 以下（タブごとのフォルダ）に分かれている。

編集は常に即座にDB(SQLite)へ保存される(Auto Save)ため、Saveボタンや
「未保存」表示は無い。ディスク破損などに備えたバックアップは、main.py側で
schedule()を使って定期的に取る。
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from task_manager_tkinter.view.settings.tk_frame import TkSettingsFrame
from task_manager_tkinter.view.task.tk_frame import TkTaskListFrame


# Called at main.py > def main()
class TkMainWindow:
    """2タブ(タスク一覧/設定)をまとめるメインウィンドウ"""

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.title("Task Manager")
        self._root.geometry("640x560")

        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(self._root)
        notebook.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.task_list_frame = TkTaskListFrame(notebook)
        self.settings_frame = TkSettingsFrame(notebook)

        notebook.add(self.task_list_frame, text="Task List")
        notebook.add(self.settings_frame, text="Settings")

    def schedule(self, delay_ms: int, callback: Callable[[], None]) -> None:
        """delay_ms ミリ秒後にcallbackを1回呼ぶ(tkinterのafter()の薄いラッパー)。
        定期的に実行したい場合は、callback自身の中で再度schedule()を呼べばよい
        （main.pyの定期バックアップがこの使い方をしている）。
        """
        self._root.after(delay_ms, callback)

    def run(self) -> None:
        self._root.mainloop()
