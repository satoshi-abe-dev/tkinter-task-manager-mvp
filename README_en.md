# mvp-pattern-sample-2

English | [日本語](README_ja.md)

A sample implementation of the MVP (Model-View-Presenter) design pattern in Python using Tkinter.
This is a follow-up to [mvp-pattern-sample-1](https://github.com/yanyayanyan1988/mvp-pattern-sample-1),
built around a more realistic, business-style, tabbed task-management app.

## Screenshots

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
    not-started→...→overdue) rather than alphabetically. Tasks with a blank value in the sorted
    column always sink to the bottom, regardless of sort direction.
  - "+ Add" and "− Delete" buttons sit below the table, joined together and stretched to span the
    table's full width. There is no separate registration form.
    - "+ Add" appends a task with every field blank and selects it. Only the task name isn't left
      blank — it gets a placeholder name like "Task N", where N is the task's own unique id (so the
      name never collides with a previous one, even after deletions). From there you fill in the
      assignee, due date, priority, and status the same way as any other row: inline editing. The
      existing rows' order (including any active sort result) is left untouched — the new task is
      always appended at the very end.
    - "− Delete" is only enabled when at least one row is selected. It supports multi-select
      (Shift/Cmd-click), and deletes every selected row at once. It shows a native confirmation
      alert; choosing "Yes" deletes the selected row(s).
  - "Export" and "Import" buttons (below the "+ Add" button) export tasks to a CSV file, or import
    them from one. CSV import keeps whatever status is written in the file as-is — the auto-set
    behavior described below does not run on import (the visual highlight is still applied
    separately, based on the due date).
  - Editing the due date inline to a past date auto-sets that task's status to "Overdue" — but only
    at that one moment (excluding "Done" tasks). It isn't enforced continuously: if the user later
    changes the status to something else manually, that choice is respected until the due date is
    edited again.
  - A row whose status is manually set to "Overdue" is always highlighted red, regardless of its due
    date (excluding "Done" tasks).
- **Settings tab**: configures the due-date highlight (on/off, and how many days ahead to warn).
  - Changing a value shows "Unsaved changes"; nothing is applied until "Save Changes" is clicked.
    The one exception is the highlight on/off checkbox itself — toggling it applies immediately to
    the task list's highlighting, without waiting for "Save Changes".
  - This setting directly drives the due-date highlight on the task list (rows for tasks that are
    overdue or due soon are shaded orange/red). Tasks with a "Done" status are excluded.

Tabs and buttons deliberately keep the OS-native look (the default `ttk.Notebook` / `ttk.Button` style).

## Folder Structure

```
task_manager_tkinter/
    main.py                   Entry point (same level as Model, View, Presenter)
    test_presenter.py         Unit tests for the two Presenters (no tkinter required)
    Model/
        task/
            task.py             Task (data class)
            task_model.py       TaskModel
            csv_io.py            CSV export/import (pure I/O, no tkinter dependency)
        settings/
            settings_model.py   Settings (data class) / SettingsModel
    View/
        task/
            task_list_view.py       TaskListView (abstract class)
            tk_task_list_frame.py   Tkinter implementation (Task List tab)
        settings/
            settings_view.py        SettingsView (abstract class)
            tk_settings_frame.py    Tkinter implementation (Settings tab)
        tk_main_window.py      Tkinter implementation (the window that combines both tabs)
    Presenter/
        task/
            task_list_presenter.py
        settings/
            settings_presenter.py
```

Model, View, and Presenter are all split into per-tab subfolders (`task`/`settings`). The one
exception is `View/tk_main_window.py`, which combines both tabs and so stays directly under `View/`.

## Responsibility of Each Layer

| Layer | Class | Responsibility | Depends on |
|---|---|---|---|
| Model | `TaskModel` | Holds, adds (including blank tasks), updates, and deletes tasks only. Knows nothing about the UI. | none |
| Model | `SettingsModel` | Holds and updates settings only (in-memory, not persisted). | none |
| Model | `csv_io` | Exports/imports tasks to/from CSV. Pure I/O functions. | none |
| View (abstract) | `TaskListView` / `SettingsView` | Define the "contract" for each tab (rendering, reading input, registering handlers). | none |
| View (impl) | `tk_task_list_frame.py` (`TkTaskListFrame`) / `tk_settings_frame.py` (`TkSettingsFrame`) / `tk_main_window.py` (`TkMainWindow`) | Concrete implementation of the above abstractions using Tkinter (`ttk.Notebook` + standard widgets). | the View abstractions, tkinter |
| Presenter | `TaskListPresenter` / `SettingsPresenter` | Holds the "screen behavior" logic for each tab: validation, updating the Model, tracking the list's sort state, adding/deleting tasks, CSV export/import, and determining the due-date highlight. `TaskListPresenter` also reads `SettingsModel` to get the highlight criteria (on/off, how many days ahead). | the corresponding Model(s) (`TaskListPresenter` depends on both `TaskModel` and `SettingsModel`), the corresponding View (abstract only) |

Because each Presenter depends only on its View abstraction, swapping the View implementation (Tkinter / another GUI library / a fake View for testing) requires no change to the Presenter code.

## Data Flow (clicking "+ Add")

1. The user clicks "+ Add" on the "Task List" tab.
2. The handler registered with `TkTaskListFrame` (`TaskListPresenter.on_add_click`) is invoked.
3. The Presenter calls `TaskModel.add_blank_task()`. The Model adds a task with every field blank,
   automatically filling the name with a placeholder like "Task N" using the id it just assigned.
4. It calls `refresh()` to update the list, then `view.select_task(task.id)` to select the new row.
   The existing rows' order (including any active sort result) is left untouched — only the new
   task is appended at the end.
5. The user double-clicks cells on that selected row to fill in the assignee, due date, priority, and
   status via the same inline-editing mechanism used for any other task.

## How to Run

`tkcalendar` is required (used for the due-date calendar picker), so set up a virtual environment at the
repository root first. Since this is a GUI app, run it in an environment where Tcl/Tk is available.

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cd task_manager_tkinter
../.venv/bin/python main.py
```

Windows (Command Prompt / PowerShell):

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

cd task_manager_tkinter
..\.venv\Scripts\python main.py
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

### A note on Windows

The code only uses cross-platform `tkinter`/`ttk`/`tkcalendar` APIs and has no macOS-only dependency, so it
should run on Windows too (development and testing were only done on macOS, though).

- The official python.org Windows installer bundles Tcl/Tk, so there's no equivalent of
  `brew install python-tk@3.14` to install separately
- The commands above include a Windows-specific variant
- The Settings tab's section header uses `font=("Helvetica", 10, "bold")`; "Helvetica" isn't a standard
  Windows font, but Tk silently falls back to a substitute font instead of raising an error when the
  requested family isn't available, so this only affects appearance, not functionality
