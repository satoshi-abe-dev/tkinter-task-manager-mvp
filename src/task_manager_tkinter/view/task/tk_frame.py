"""
View (Tkinter implementation layer) — task list tab
--------------------------------------------------------
Concrete Tkinter implementation of TaskListView (view/task/contract.py).
Tkinter dependency confined to this file and view/settings/tk_frame.py.
"""

import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Dict, List, Optional

from tkcalendar import Calendar

from task_manager_tkinter.model.task import PRIORITIES, STATUSES, Task
from task_manager_tkinter.view.callbacks import CallbackRegistryMixin
from task_manager_tkinter.view.task.contract import TaskListView

_DATE_PATTERN = "yyyy-mm-dd"

_COLUMNS = ("name", "assignee", "due_date", "priority", "status")
_COLUMN_LABELS = {
    "name": "Task Name",
    "assignee": "Assignee",
    "due_date": "Due Date",
    "priority": "Priority",
    "status": "Status",
}


# Inheritance order: concrete widget (ttk.Frame) -> mixin (callback machinery) -> contract (ABC)
class TkTaskListFrame(ttk.Frame, CallbackRegistryMixin, TaskListView):
    """Implementation of the "Task List" tab (ttk.Treeview). Double-click a
    cell to edit inline; commits are delegated to the Presenter (this View
    never touches the Model directly)."""

    PRIORITIES = PRIORITIES
    STATUSES = STATUSES

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, padding=16)
        self._editor: Optional[tk.Widget] = None
        self._date_picker: Optional[tk.Toplevel] = None

        # Default row height (~18px) clips the inline-editing overlay's text
        style = ttk.Style(self)
        style.configure("TaskList.Treeview", rowheight=28)

        # Row 0 (table) absorbs extra space; rows 1-2 (buttons) pin to content height
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)

        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)  # The table's column absorbs extra space
        tree_frame.columnconfigure(1, weight=0)  # The scrollbar's column stays at its content width
        tree_frame.rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(
            tree_frame, columns=_COLUMNS, show="headings", height=12, style="TaskList.Treeview"
        )
        for col in _COLUMNS:
            self._tree.heading(
                col, text=_COLUMN_LABELS[col], command=self._make_heading_handler(col)
            )
            self._tree.column(col, width=110, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        # Row tags for near/past due dates — unlike ttk.Label, Treeview row
        # tags reliably apply background color on Aqua
        self._tree.tag_configure("warning", background="#fbeed7", foreground="#b8790f")
        self._tree.tag_configure("overdue", background="#fbe4e4", foreground="#d94f4f")

        self._tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        button_row = ttk.Frame(self)
        button_row.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        button_row.columnconfigure(0, weight=1)
        button_row.columnconfigure(1, weight=1)

        self._add_button = ttk.Button(
            button_row, text="+ Add", command=self._handle_add_click
        )
        self._add_button.grid(row=0, column=0, sticky="ew")
        self._delete_button = ttk.Button(
            button_row, text="− Delete", command=self._handle_delete_click, state="disabled"
        )
        self._delete_button.grid(row=0, column=1, sticky="ew")

        csv_row = ttk.Frame(self)
        csv_row.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self._export_button = ttk.Button(
            csv_row, text="Export", command=self._handle_export_click
        )
        self._export_button.grid(row=0, column=0, padx=(0, 8))
        self._import_button = ttk.Button(
            csv_row, text="Import", command=self._handle_import_click
        )
        self._import_button.grid(row=0, column=1)

        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<Button-1>", self._on_click)
        self._tree.bind("<<TreeviewSelect>>", self._on_selection_changed)

    def _make_heading_handler(self, field: str) -> Callable[[], None]:
        def handler() -> None:
            self._fire("column_clicked", field)

        return handler

    # Override
    def show_tasks(self, tasks: List[Task]) -> None:
        self._destroy_editor()
        self._tree.delete(*self._tree.get_children())
        for t in tasks:
            self._tree.insert(
                "",
                "end",
                iid=str(t.id),
                values=(t.name, t.assignee, t.due_date, t.priority, t.status),
            )

    # Override
    def set_on_cell_edited(self, handler: Callable[[int, str, str], None]) -> None:
        self._set_callback("cell_edited", handler)

    # Override
    def set_on_column_clicked(self, handler: Callable[[str], None]) -> None:
        self._set_callback("column_clicked", handler)

    # Override
    def show_sort_state(self, field: Optional[str], ascending: bool) -> None:
        for col in _COLUMNS:
            text = _COLUMN_LABELS[col]
            if col == field:
                text += " ▲" if ascending else " ▼"
            self._tree.heading(col, text=text)

    # Override
    def set_on_add_click(self, handler: Callable[[], None]) -> None:
        self._set_callback("add_click", handler)

    # Override
    def set_on_delete_click(self, handler: Callable[[List[int]], None]) -> None:
        self._set_callback("delete_click", handler)

    # Override
    def select_task(self, task_id: int) -> None:
        iid = str(task_id)
        if self._tree.exists(iid):
            self._tree.selection_set(iid)
            self._tree.see(iid)
            self._tree.focus(iid)

    # Override
    def show_due_date_highlights(self, highlights: Dict[int, str]) -> None:
        for iid in self._tree.get_children():
            tag = highlights.get(int(iid))
            self._tree.item(iid, tags=(tag,) if tag else ())

    # Override
    def set_on_export_click(self, handler: Callable[[], None]) -> None:
        self._set_callback("export_click", handler)

    # Override
    def set_on_import_click(self, handler: Callable[[], None]) -> None:
        self._set_callback("import_click", handler)

    # Override
    def ask_save_path(self) -> Optional[str]:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")]
        )
        return path or None

    # Override
    def ask_open_path(self) -> Optional[str]:
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        return path or None

    # Override
    def show_message(self, title: str, message: str) -> None:
        messagebox.showinfo(title=title, message=message)

    def _handle_export_click(self) -> None:
        self._fire("export_click")

    def _handle_import_click(self) -> None:
        self._fire("import_click")

    def _on_selection_changed(self, event: tk.Event) -> None:
        state = "normal" if self._tree.selection() else "disabled"
        self._delete_button.config(state=state)

    def _handle_add_click(self) -> None:
        self._fire("add_click")

    def _handle_delete_click(self) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        task_ids = [int(row_id) for row_id in selection]

        if len(selection) == 1:
            name = self._tree.set(selection[0], "name")
            message = f'Delete "{name}"?\nThis action cannot be undone.'
        else:
            message = f"Delete {len(selection)} selected task(s)?\nThis action cannot be undone."

        confirmed = messagebox.askyesno("Confirm", message)
        if confirmed:
            self._fire("delete_click", task_ids)

    def _on_click(self, event: tk.Event) -> None:
        # Clicking empty space clears selection; the heading area is excluded (used for sorting)
        if self._tree.identify_region(event.x, event.y) == "nothing":
            self._tree.selection_remove(*self._tree.selection())

    def _on_double_click(self, event: tk.Event) -> None:
        if self._tree.identify_region(event.x, event.y) != "cell":
            return
        row_id = self._tree.identify_row(event.y)
        col_id = self._tree.identify_column(event.x)  # e.g. "#1"
        if not row_id or not col_id:
            return
        col_index = int(col_id.replace("#", "")) - 1
        if col_index < 0 or col_index >= len(_COLUMNS):
            return
        field = _COLUMNS[col_index]
        bbox = self._tree.bbox(row_id, col_id)
        if not bbox:
            return

        task_id = int(row_id)
        x, y, width, height = bbox
        current_value = self._tree.set(row_id, field)

        self._destroy_editor()

        # due_date uses a separate calendar popup, not a cell overlay:
        # tkcalendar.DateEntry's undecorated window mis-renders ttk text
        # color on Aqua; a plain decorated Toplevel avoids that.
        if field == "due_date":
            self._open_date_picker(task_id, row_id, current_value)
            return

        editor: tk.Widget
        if field in ("priority", "status"):
            values = self.PRIORITIES if field == "priority" else self.STATUSES
            combobox = ttk.Combobox(self._tree, values=values, state="readonly")
            combobox.set(current_value)
            combobox.bind("<<ComboboxSelected>>", lambda e: commit())
            editor = combobox
        else:
            entry = ttk.Entry(self._tree)
            entry.insert(0, current_value)
            entry.select_range(0, "end")
            editor = entry

        # Slightly oversize/shift to leave room for the editor's own focus border
        pad_x, pad_y = 3, 2
        editor.place(
            x=x - pad_x,
            y=y - pad_y,
            width=width + pad_x * 2,
            height=height + pad_y * 2,
        )
        editor.focus_set()

        def commit(_event: Optional[tk.Event] = None) -> None:
            new_value = editor.get()  # type: ignore[attr-defined]
            self._destroy_editor()
            if new_value != current_value:
                self._fire("cell_edited", task_id, field, new_value)

        def cancel(_event: Optional[tk.Event] = None) -> None:
            self._destroy_editor()

        editor.bind("<Return>", commit)
        editor.bind("<Escape>", cancel)
        editor.bind("<FocusOut>", commit)

        self._editor = editor

    def _open_date_picker(self, task_id: int, row_id: str, current_value: str) -> None:
        self._destroy_editor()  # close any already-open picker instead of stacking

        popup = tk.Toplevel(self)
        self._date_picker = popup
        popup.bind(
            "<Destroy>",
            lambda e: setattr(self, "_date_picker", None) if e.widget is popup else None,
        )
        popup.title("Select Due Date")
        popup.transient(self.winfo_toplevel())
        popup.resizable(False, False)

        # Aqua ignores background-color on custom ttk styles, so tkcalendar's
        # default white-on-white text and selectbackground highlight both
        # disappear; force text/select colors instead. TButton's background
        # IS respected on Aqua, so lighten it too (default gray30 hides the
        # black arrows).
        calendar_kwargs = {
            "selectmode": "day",
            "date_pattern": _DATE_PATTERN,
            "locale": "en_US",  # match month/weekday names to the GUI's language
            "showweeknumbers": False,
            "foreground": "black",
            "selectforeground": "#d94f4f",
            "background": "white",
        }
        initial = None
        try:
            initial = datetime.strptime(current_value, "%Y-%m-%d").date()
            calendar_kwargs.update(year=initial.year, month=initial.month, day=initial.day)
        except ValueError:
            pass  # Unparseable value: just show the current month as-is

        popup.columnconfigure(0, weight=1)

        # Shown as text since the calendar's own highlight disappears after navigating away
        info_row = ttk.Frame(popup)
        info_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        info_row.columnconfigure(0, weight=1)  # label stretches; back button hugs the right edge
        info_label = ttk.Label(info_row, text=f"Current due date: {current_value or 'Not set'}")
        info_label.grid(row=0, column=0, sticky="w")

        calendar = Calendar(popup, **calendar_kwargs)
        calendar.grid(row=1, column=0, padx=10, pady=10)
        # selectbackground/border don't work on Aqua either; emphasize the
        # selected day via font color/weight/size instead, rewriting the
        # style directly since tkcalendar has no constructor arg for it.
        base_font = calendar._font.actual()
        base_size = base_font["size"]
        larger_size = base_size + 4 if base_size >= 0 else base_size - 4
        calendar.style.configure(
            "sel.%s.TLabel" % calendar._style_prefixe,
            font=(base_font["family"], larger_size, "bold"),
        )

        if initial is not None:
            back_button = ttk.Button(
                info_row,
                text="Back to This Date",
                command=lambda: calendar.selection_set(initial),
            )
            back_button.grid(row=0, column=1, sticky="e")

        # Finalize the widgets' real sizes before computing the geometry (position)
        popup.update_idletasks()

        def on_selected(_event: Optional[tk.Event] = None) -> None:
            new_value = calendar.get_date()
            popup.destroy()
            if new_value != current_value:
                self._fire("cell_edited", task_id, "due_date", new_value)

        calendar.bind("<<CalendarSelected>>", on_selected)
        popup.bind("<Escape>", lambda e: popup.destroy())
        popup.protocol("WM_DELETE_WINDOW", popup.destroy)

        bbox = self._tree.bbox(row_id, "due_date")
        if bbox:
            cell_x, cell_y, _cell_w, cell_h = bbox
            popup.geometry(
                f"+{self._tree.winfo_rootx() + cell_x}+{self._tree.winfo_rooty() + cell_y + cell_h}"
            )

        popup.lift()
        popup.attributes("-topmost", True)
        popup.after(200, lambda: popup.attributes("-topmost", False))
        popup.grab_set()
        popup.focus_set()

    def _destroy_editor(self) -> None:
        if self._editor is not None:
            self._editor.destroy()
            self._editor = None
        if self._date_picker is not None:
            self._date_picker.destroy()
            self._date_picker = None
