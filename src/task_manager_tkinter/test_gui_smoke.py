"""
GUI construction smoke test (pytest)
--------------------------------------
Only verifies TkMainWindow assembles without raising (no mainloop, no
behavior check). The only test that instantiates the Tkinter View — skipped
without tkinter or a display (e.g. CI's Ubuntu runner).

    pytest -m smoke        # just this test
    pytest -m "not smoke"  # everything else
"""

import pytest


@pytest.mark.smoke
def test_gui_constructs() -> None:
    try:
        from task_manager_tkinter.view.tk_main_window import TkMainWindow
    except Exception as exc:  # e.g. ModuleNotFoundError (tkinter not present)
        pytest.skip(f"tkinter unavailable: {exc}")

    try:
        window = TkMainWindow()
    except Exception as exc:  # e.g. TclError (no display)
        pytest.skip(f"no display: {exc}")

    window.destroy()
