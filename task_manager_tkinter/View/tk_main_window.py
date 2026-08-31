"""
View（Tkinter実装層）— ウィンドウ全体
--------------------------------------
タスク一覧タブ(TkTaskListFrame)・設定タブ(TkSettingsFrame)をttk.Notebookに
まとめ、ウィンドウ全体の起動(run)を担う。各タブ自体の実装はView/task/、
View/settings/ 以下（タブごとのフォルダ）に分かれている。

Saveボタンはどちらのタブの中にも置かず、Notebookの直前の行（タブの外）に
1つだけ配置している。押すと両タブの変更をまとめて保存する（実際に何を
保存するかの判断はこのクラスの外、main.py側で行う）。
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

        self._on_save_click: Optional[Callable[[], None]] = None

        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=0)  # Save行
        self._root.rowconfigure(1, weight=1)  # タブ本体

        # Saveボタン。タブの直前(Notebookの上)、行の右端に配置する。中間に空の
        # Frameを挟まず直接gridし、sticky="ne"で右上に寄せることで、ボタン単体の
        # 行が実際以上に広い余白の帯に見えないよう、上下の余白を切り詰めている。
        self._save_button = ttk.Button(self._root, text="Save", command=self._handle_save_click)
        self._save_button.grid(row=0, column=0, sticky="ne", padx=8, pady=(6, 4))

        notebook = ttk.Notebook(self._root)
        notebook.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

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

    def set_on_save_click(self, handler: Callable[[], None]) -> None:
        """Saveボタン押下時に呼ばれるハンドラを登録する。
        実際に何を保存するか（どのPresenterのon_save_click()を呼ぶか）は
        ハンドラの責任（main.py側で両タブ分をまとめて呼ぶ）。
        """
        self._on_save_click = handler

    def _handle_save_click(self) -> None:
        if self._on_save_click:
            self._on_save_click()

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
