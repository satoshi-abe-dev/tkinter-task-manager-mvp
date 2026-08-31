# mvp-pattern-sample-2

English | [日本語](README_ja.md)

A sample implementation of the MVP (Model-View-Presenter) design pattern in Python using Tkinter.
This is a follow-up to [mvp-pattern-sample-1](https://github.com/yanyayanyan1988/mvp-pattern-sample-1),
built around a more realistic, business-style, tabbed task-management app.

## Screenshots

> ⚠️ These are from an older version that still had a "New Task" tab. The app now has just two tabs
> (Task List / Settings) as described below. Screenshots will be replaced once retaken.

| Task List | Settings |
|---|---|
| ![Task list tab](docs/screenshots/task-list.png) | ![Settings tab](docs/screenshots/settings.png) |

## Purpose

A sample project built around a Tkinter desktop app that could plausibly exist in a real workplace —
one with tabs for a task list and settings — implemented with responsibilities separated according
to the MVP pattern (Model / View / Presenter).

## Features

- **Task List tab**: shows all registered tasks in a table (`ttk.Treeview`).
  - Double-click a cell to edit it inline (name, assignee, due date, priority, status). Priority and
    status are edited through dropdowns so invalid values can't be entered.
  - The due date is picked from a `tkcalendar` calendar popup. The popup always shows the "current due
    date" as text, and a "Back to this date" button lets you find your way back after browsing to a
    different month.
  - Click a column header to sort by that column; click it again to toggle ascending/descending (shown
    as ▲/▼ in the header). Priority and status sort by their meaningful order (low→mid→high,
    not-started→...→overdue) rather than alphabetically.
  - "＋ Add" and "－ Delete" buttons sit below the table, joined together and stretched to span the
    table's full width. There is no separate registration form.
    - "＋ Add" appends a task with every field blank and selects it. Only the task name isn't left
      blank — it gets a placeholder name like "Task N", where N is the task's own unique id (so the
      name never collides with a previous one, even after deletions). From there you fill in the
      assignee, due date, priority, and status the same way as any other row: inline editing.
    - "－ Delete" is only enabled when a row is selected. It shows a native confirmation alert
      ("Are you sure you want to delete this?"); choosing "Yes" deletes the selected row.
- **Settings tab**: configure notifications (on/off and timing), the list page size, and the theme.
  - Changing a value shows "You have unsaved changes"; nothing is applied until "Save changes" is clicked.
  - Tasks can be exported to a CSV file, or imported from one.

Tabs and buttons deliberately keep the OS-native look (the default `ttk.Notebook` / `ttk.Button` style).

## Folder Structure

```
task_manager_tkinter/
    main.py                   Entry point (same level as Model, View, Presenter)
    test_presenter.py         Unit tests for the two Presenters (no tkinter required)
    Model/
        task.py                Task (data class)
        task_model.py          TaskModel
        settings_model.py      Settings (data class) / SettingsModel
        csv_io.py               CSV export/import (pure I/O, no tkinter dependency)
    View/
        task_list_view.py      TaskListView (abstract class)
        settings_view.py       SettingsView (abstract class)
        tk_main_window.py      Tkinter implementation (the two tab Frames + the window)
    Presenter/
        task_list_presenter.py
        settings_presenter.py
```

## Responsibility of Each Layer

| Layer | Class | Responsibility | Depends on |
|---|---|---|---|
| Model | `TaskModel` | Holds, adds (including blank tasks), updates, and deletes tasks only. Knows nothing about the UI. | none |
| Model | `SettingsModel` | Holds and updates settings only (in-memory, not persisted). | none |
| Model | `csv_io` | Exports/imports tasks to/from CSV. Pure I/O functions. | none |
| View (abstract) | `TaskListView` / `SettingsView` | Define the "contract" for each tab (rendering, reading input, registering handlers). | none |
| View (impl) | `tk_main_window.py` (`TkTaskListFrame` / `TkSettingsFrame` / `TkMainWindow`) | Concrete implementation of the above abstractions using Tkinter (`ttk.Notebook` + standard widgets). | the View abstractions, tkinter |
| Presenter | `TaskListPresenter` / `SettingsPresenter` | Holds the "screen behavior" logic for each tab: validation, updating the Model, tracking the list's sort state, and adding/deleting tasks. | the corresponding Model(s), the corresponding View (abstract only) |

Because each Presenter depends only on its View abstraction, swapping the View implementation (Tkinter / another GUI library / a fake View for testing) requires no change to the Presenter code.

## Data Flow (clicking "＋ Add")

1. The user clicks "＋ Add" on the "Task List" tab.
2. The handler registered with `TkTaskListFrame` (`TaskListPresenter.on_add_click`) is invoked.
3. The Presenter calls `TaskModel.add_blank_task()`. The Model adds a task with every field blank,
   automatically filling the name with a placeholder like "Task N" using the id it just assigned.
4. It calls `refresh()` to update the list, then `view.select_task(task.id)` to select the new row.
5. The user double-clicks cells on that selected row to fill in the assignee, due date, priority, and
   status via the same inline-editing mechanism used for any other task.

## How to Run

`tkcalendar` is required (used for the due-date calendar picker), so set up a virtual environment at the
repository root first. Since this is a GUI app, run it in an environment where Tcl/Tk is available.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cd task_manager_tkinter
../.venv/bin/python main.py
```

## How to Test

By swapping in fake Views (fake implementations of each View abstract class) instead of `TkMainWindow`
(and its internal Frames), the two Presenters' logic can be verified without ever starting Tkinter.

`test_presenter.py` depends only on the `View.*_view` abstract classes and never imports `View.tk_main_window`
(the Tkinter implementation), so it runs fine even in environments without tkinter installed.

```bash
cd task_manager_tkinter
python3 test_presenter.py
```

CI also runs the same tests automatically on every pull request and every push to `main` (see `.github/workflows/test.yml`).

## Prerequisites

- Python 3.14 (Homebrew build)
- Using tkinter requires `brew install python-tk@3.14` separately (the deprecated Tcl/Tk 8.5.9 bundled with macOS's `/usr/bin` Python is not used)
- Running the GUI requires `tkcalendar` (see `requirements.txt`). Not needed to run `test_presenter.py`.
