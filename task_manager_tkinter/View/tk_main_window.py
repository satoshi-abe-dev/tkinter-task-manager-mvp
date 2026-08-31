"""
View（Tkinter実装層）— ウィンドウ全体
--------------------------------------
タスク一覧タブ(TkTaskListFrame)・設定タブ(TkSettingsFrame)をttk.Notebookに
まとめ、ウィンドウ全体の起動(run)を担う。各タブ自体の実装はView/task/、
View/settings/ 以下（タブごとのフォルダ）に分かれている。
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from View.settings.tk_settings_frame import TkSettingsFrame
from View.task.tk_task_list_frame import TkTaskListFrame


# Called at main.py > def main()
class TkMainWindow:
    """2タブ(タスク一覧/設定)をまとめるメインウィンドウ"""

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.title("Task Manager")
        self._root.geometry("640x580")

        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(self._root)
        notebook.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.task_list_frame = TkTaskListFrame(notebook)
        self.settings_frame = TkSettingsFrame(notebook)

        notebook.add(self.task_list_frame, text="Task List")
        notebook.add(self.settings_frame, text="Settings")

        self._on_close_requested: Optional[Callable[[], None]] = None
        # ウィンドウを閉じようとした時(タイトルバーの×、Cmd+Qなど)、いきなり
        # 終了させず、まず外部(main.py)に登録されたハンドラに判断を委ねる。
        # 未保存の変更があるかどうかはModelの話なので、View側であるこのクラスは
        # 一切知らない（知っているのはハンドラを登録する側）。
        self._root.protocol("WM_DELETE_WINDOW", self._handle_close_request)

    def set_on_close_requested(self, handler: Callable[[], None]) -> None:
        """ウィンドウを閉じようとした時に呼ばれるハンドラを登録する。
        実際に閉じるかどうかの判断・close()の呼び出しはハンドラの責任。
        """
        self._on_close_requested = handler

    def _handle_close_request(self) -> None:
        if self._on_close_requested:
            self._on_close_requested()
        else:
            self.close()

    def ask_save_discard_cancel(self, title: str, message: str) -> Optional[bool]:
        """「保存する/破棄する/キャンセル」の3択ダイアログを表示する。
        戻り値: True=保存する、False=破棄する、None=キャンセル
        """
        return messagebox.askyesnocancel(title=title, message=message)

    def close(self) -> None:
        """ウィンドウを実際に閉じ、アプリを終了する"""
        self._root.destroy()

    def run(self) -> None:
        self._root.mainloop()
