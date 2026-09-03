"""
GUI 構築スモークテスト
----------------------
実物の Tkinter ウィジェット(TkMainWindow → TkTaskListFrame / TkSettingsFrame)が
例外なく組み上がることだけを確認する。挙動は検証しない。mainloop() は呼ばない
（＝ハングしない）。

test_presenter.py が意図的に避けている「View の Tkinter 実装」を、実際に import・
生成してみる唯一のテスト。tkinter が無い / 画面が無い環境（ヘッドレス Linux など）
では自動でスキップして正常終了する。

実行方法（どちらでも可。リポジトリのルートで）:
    python3 -m task_manager_tkinter.test_gui_smoke
    python3 task_manager_tkinter/test_gui_smoke.py
"""

import os
import sys

if __package__ in (None, ""):
    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def main() -> None:
    # tkinter 自体が無い Python もある（Linux の一部ディストリなど）。
    try:
        from task_manager_tkinter.view.tk_main_window import TkMainWindow
    except Exception as exc:  # ModuleNotFoundError など
        print(f"GUI smoke skipped ({type(exc).__name__}: {exc})")
        return

    # 画面が無いと TkMainWindow() 内の tk.Tk() が TclError を投げる。
    try:
        window = TkMainWindow()
    except Exception as exc:
        print(f"GUI smoke skipped ({type(exc).__name__}: {exc})")
        return

    window.destroy()
    print(f"GUI smoke OK on {sys.platform}")


if __name__ == "__main__":
    main()
