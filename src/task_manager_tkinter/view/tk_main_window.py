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

_WINDOW_WIDTH = 640
_WINDOW_HEIGHT = 560


# Called at main.py > def main()
class TkMainWindow:
    """2タブ(タスク一覧/設定)をまとめるメインウィンドウ"""

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
        """指定サイズのウィンドウを画面中央に配置する。

        geometry() にサイズだけ渡すと初期位置はウィンドウマネージャ任せに
        なり、環境によっては左下などに寄る。画面の幅・高さから左上座標を
        計算して "WxH+X+Y" 形式で明示する。

        macOS では、ウィンドウが実体化する前に座標付き geometry() を渡しても
        初回表示時にマネージャの既定位置で上書きされてしまう。全ウィジェットを
        組んだ後 update_idletasks() で一度実体化させてから座標を指定する。
        """
        self._root.update_idletasks()
        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()
        x = max((screen_width - width) // 2, 0)
        y = max((screen_height - height) // 2, 0)
        self._root.geometry(f"{width}x{height}+{x}+{y}")

    def schedule(self, delay_ms: int, callback: Callable[[], None]) -> None:
        """delay_ms ミリ秒後にcallbackを1回呼ぶ(tkinterのafter()の薄いラッパー)。
        定期的に実行したい場合は、callback自身の中で再度schedule()を呼べばよい
        （main.pyの定期バックアップがこの使い方をしている）。
        """
        self._root.after(delay_ms, callback)

    def run(self) -> None:
        self._root.mainloop()

    def destroy(self) -> None:
        """ウィンドウを破棄する（run() を回さずに片付けたいとき用。
        GUI 構築スモークテストが使う）。"""
        self._root.destroy()
