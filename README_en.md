# mvp-pattern-sample-2

English | [日本語](README_ja.md)

A sample implementation of the MVP (Model-View-Presenter) design pattern in Python using Tkinter.
This is a follow-up to [mvp-pattern-sample-1](https://github.com/yanyayanyan1988/mvp-pattern-sample-1),
built around a more realistic, business-style, tabbed task-management app.

## Screenshots

| Task List | New Task | Settings |
|---|---|---|
| ![Task list tab](docs/screenshots/task-list.png) | ![New task tab](docs/screenshots/new-task.png) | ![Settings tab](docs/screenshots/settings.png) |

## Purpose

A sample project built around a Tkinter desktop app that could plausibly exist in a real workplace —
one with tabs for a task list, a registration form, and settings — implemented with responsibilities
separated according to the MVP pattern (Model / View / Presenter).

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
- **New Task tab**: register a task with a name, assignee, due date, priority, initial status, tags, and a memo.
  - If the task name is left empty, an error message is shown and the task is not registered.
  - "Cancel" clears the form.
- **Settings tab**: configure notifications (on/off and timing), the default assignee, the list page size, and the theme.
  - Changing a value shows "You have unsaved changes"; nothing is applied until "Save changes" is clicked.
  - Tasks can be exported to a CSV file, or imported from one.

Tabs deliberately keep the OS-native look (the default `ttk.Notebook` style).

## Folder Structure

```
task_manager_tkinter/
    main.py                   Entry point (same level as Model, View, Presenter)
    test_presenter.py         Unit tests for the three Presenters (no tkinter required)
    Model/
        task.py                Task (data class)
        task_model.py          TaskModel
        settings_model.py      Settings (data class) / SettingsModel
        csv_io.py               CSV export/import (pure I/O, no tkinter dependency)
    View/
        task_list_view.py      TaskListView (abstract class)
        new_task_view.py       NewTaskView (abstract class)
        settings_view.py       SettingsView (abstract class)
        tk_main_window.py      Tkinter implementation (the three tab Frames + the window)
    Presenter/
        task_list_presenter.py
        new_task_presenter.py
        settings_presenter.py
```

## Responsibility of Each Layer

| Layer | Class | Responsibility | Depends on |
|---|---|---|---|
| Model | `TaskModel` | Holds, adds, and updates tasks (for inline editing in the list) only. Knows nothing about the UI. | none |
| Model | `SettingsModel` | Holds and updates settings only (in-memory, not persisted). | none |
| Model | `csv_io` | Exports/imports tasks to/from CSV. Pure I/O functions. | none |
| View (abstract) | `TaskListView` / `NewTaskView` / `SettingsView` | Define the "contract" for each tab (rendering, reading input, registering handlers). | none |
| View (impl) | `tk_main_window.py` (`TkTaskListFrame` / `TkNewTaskFrame` / `TkSettingsFrame` / `TkMainWindow`) | Concrete implementation of the above abstractions using Tkinter (`ttk.Notebook` + standard widgets). | the View abstractions, tkinter |
| Presenter | `TaskListPresenter` / `NewTaskPresenter` / `SettingsPresenter` | Holds the "screen behavior" logic for each tab: validation, updating the Model, coordinating between tabs (e.g. refreshing the list after a new task is registered), and tracking the list's sort state. | the corresponding Model(s), the corresponding View (abstract only) |

Because each Presenter depends only on its View abstraction, swapping the View implementation (Tkinter / another GUI library / a fake View for testing) requires no change to the Presenter code.

## Data Flow (registering a task from the New Task tab)

1. The user fills in the task name and other fields on the "New Task" tab and clicks "Register".
2. The handler registered with `TkNewTaskFrame` (`NewTaskPresenter.on_register_click`) is invoked.
3. The Presenter validates the task name; if it's empty, it calls `view.show_name_error(...)` and stops.
4. Otherwise, it adds the task via `TaskModel.add_task()` and clears the form with `view.clear_form()`.
5. It calls the `on_task_added` callback passed into its constructor (`TaskListPresenter.refresh`), which updates the Task List tab.

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
(and its three internal Frames), the three Presenters' logic can be verified without ever starting Tkinter.

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
