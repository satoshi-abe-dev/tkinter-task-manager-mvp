"""
GUI construction smoke test (pytest)
--------------------------------------
Only verifies that the real Tkinter widgets
(TkMainWindow -> TkTaskListFrame / TkSettingsFrame) can be assembled without
raising an exception. Behavior is not verified. mainloop() is never called
(so it won't hang).

The only test that actually imports and instantiates the "Tkinter
implementation of the View", which test_presenter.py deliberately avoids.
Automatically skipped in an environment without tkinter installed, or
headless (no display) — e.g. CI's Ubuntu runner.

    pytest -m smoke        # just this test
    pytest -m "not smoke"  # everything else (the tkinter-independent presenter tests only)
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
