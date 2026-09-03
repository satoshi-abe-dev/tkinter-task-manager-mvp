"""
GUI 構築スモークテスト（pytest）
--------------------------------
実物の Tkinter ウィジェット(TkMainWindow → TkTaskListFrame / TkSettingsFrame)が
例外なく組み上がることだけを確認する。挙動は検証しない。mainloop() は呼ばない
（＝ハングしない）。

test_presenter.py が意図的に避けている「View の Tkinter 実装」を、実際に import・
生成してみる唯一のテスト。tkinter が入っていない、またはヘッドレス[画面の無い]
環境（CI の Ubuntu ランナーなど）では自動で skip する。

    pytest -m smoke        # このテストだけ
    pytest -m "not smoke"  # これ以外（tkinter 非依存の presenter テストだけ）
"""

import pytest


@pytest.mark.smoke
def test_gui_constructs() -> None:
    try:
        from task_manager_tkinter.view.tk_main_window import TkMainWindow
    except Exception as exc:  # ModuleNotFoundError など（tkinter が無い）
        pytest.skip(f"tkinter unavailable: {exc}")

    try:
        window = TkMainWindow()
    except Exception as exc:  # TclError など（画面が無い）
        pytest.skip(f"no display: {exc}")

    window.destroy()
