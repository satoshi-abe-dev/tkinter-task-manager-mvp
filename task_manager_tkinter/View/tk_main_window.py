"""
View（Tkinter実装層）
---------------------
task_list_view / new_task_view / settings_view の3つの抽象クラスを、
Tkinterを使って具体的に実装する層。Tkinterへの依存はこのファイルだけに閉じ込める。

タブ1枚 = 1つのフレームクラスとして実装し、それぞれ対応する抽象Viewを継承する。
TkMainWindowはそれらをttk.Notebookにまとめ、ウィンドウ全体の起動(run)を担う。
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, List, Optional

from Model.settings_model import Settings
from Model.task import Task
from View.new_task_view import NewTaskView
from View.settings_view import SettingsView
from View.task_list_view import TaskListView

_COLUMNS = ("name", "assignee", "due_date", "priority", "status")
_COLUMN_LABELS = {
    "name": "タスク名",
    "assignee": "担当",
    "due_date": "期限",
    "priority": "優先度",
    "status": "ステータス",
}


# Called at View/tk_main_window.py > class TkMainWindow
class TkTaskListFrame(ttk.Frame, TaskListView):
    """「タスク一覧」タブの実装。ttk.Treeviewで表形式に表示する。

    セルをダブルクリックするとインライン編集ができる。編集内容の確定は
    Presenterに委ねる（Viewはここで直接Modelを書き換えない）。
    """

    PRIORITIES = ["低", "中", "高"]
    STATUSES = ["未着手", "進行中", "完了", "遅延"]

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, padding=16)
        self._on_cell_edited: Optional[Callable[[int, str, str], None]] = None
        self._editor: Optional[tk.Widget] = None

        self._tree = ttk.Treeview(self, columns=_COLUMNS, show="headings", height=12)
        for col in _COLUMNS:
            self._tree.heading(col, text=_COLUMN_LABELS[col])
            self._tree.column(col, width=110, anchor="w")
        self._tree.pack(fill="both", expand=True)

        self._tree.bind("<Double-1>", self._on_double_click)

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
        self._on_cell_edited = handler

    def _on_double_click(self, event: tk.Event) -> None:
        if self._tree.identify_region(event.x, event.y) != "cell":
            return
        row_id = self._tree.identify_row(event.y)
        col_id = self._tree.identify_column(event.x)  # 例: "#1"
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

        editor.place(x=x, y=y, width=width, height=height)
        editor.focus_set()

        def commit(_event: Optional[tk.Event] = None) -> None:
            new_value = editor.get()  # type: ignore[attr-defined]
            self._destroy_editor()
            if new_value != current_value and self._on_cell_edited:
                self._on_cell_edited(task_id, field, new_value)

        def cancel(_event: Optional[tk.Event] = None) -> None:
            self._destroy_editor()

        editor.bind("<Return>", commit)
        editor.bind("<FocusOut>", commit)
        editor.bind("<Escape>", cancel)

        self._editor = editor

    def _destroy_editor(self) -> None:
        if self._editor is not None:
            self._editor.destroy()
            self._editor = None


class TkNewTaskFrame(ttk.Frame, NewTaskView):
    """「新規登録」タブの実装。"""

    ASSIGNEES = ["佐藤", "田中", "鈴木"]
    PRIORITIES = ["低", "中", "高"]
    STATUSES = ["未着手", "進行中"]

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, padding=16)

        self._name_var = tk.StringVar()
        self._assignee_var = tk.StringVar(value=self.ASSIGNEES[0])
        self._due_date_var = tk.StringVar()
        self._priority_var = tk.StringVar(value="中")
        self._status_var = tk.StringVar(value=self.STATUSES[0])
        self._tags_var = tk.StringVar()

        row = 0
        ttk.Label(self, text="タスク名 *").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(self, textvariable=self._name_var, width=32).grid(
            row=row, column=1, sticky="we", pady=4
        )
        row += 1
        self._name_error_label = ttk.Label(self, text="", foreground="#d94f4f")
        self._name_error_label.grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(self, text="担当者").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Combobox(
            self, textvariable=self._assignee_var, values=self.ASSIGNEES, state="readonly"
        ).grid(row=row, column=1, sticky="we", pady=4)
        row += 1

        ttk.Label(self, text="期限 (YYYY-MM-DD)").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(self, textvariable=self._due_date_var).grid(
            row=row, column=1, sticky="we", pady=4
        )
        row += 1

        ttk.Label(self, text="優先度").grid(row=row, column=0, sticky="w", pady=4)
        priority_frame = ttk.Frame(self)
        priority_frame.grid(row=row, column=1, sticky="w", pady=4)
        for p in self.PRIORITIES:
            ttk.Radiobutton(
                priority_frame, text=p, value=p, variable=self._priority_var
            ).pack(side="left", padx=(0, 10))
        row += 1

        ttk.Label(self, text="初期ステータス").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Combobox(
            self, textvariable=self._status_var, values=self.STATUSES, state="readonly"
        ).grid(row=row, column=1, sticky="we", pady=4)
        row += 1

        ttk.Label(self, text="タグ（カンマ区切り）").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(self, textvariable=self._tags_var).grid(
            row=row, column=1, sticky="we", pady=4
        )
        row += 1

        ttk.Label(self, text="メモ").grid(row=row, column=0, sticky="nw", pady=4)
        self._memo_text = tk.Text(self, width=32, height=4)
        self._memo_text.grid(row=row, column=1, sticky="we", pady=4)
        row += 1

        btn_row = ttk.Frame(self)
        btn_row.grid(row=row, column=1, sticky="e", pady=(12, 0))
        self._cancel_button = ttk.Button(btn_row, text="キャンセル")
        self._cancel_button.pack(side="left", padx=(0, 8))
        self._register_button = ttk.Button(btn_row, text="登録")
        self._register_button.pack(side="left")

        self.columnconfigure(1, weight=1)

    # Override
    def set_on_register_click(self, handler: Callable[[], None]) -> None:
        self._register_button.config(command=handler)

    # Override
    def set_on_cancel_click(self, handler: Callable[[], None]) -> None:
        self._cancel_button.config(command=handler)

    # Override
    def get_form_values(self) -> dict:
        return {
            "name": self._name_var.get(),
            "assignee": self._assignee_var.get(),
            "due_date": self._due_date_var.get(),
            "priority": self._priority_var.get(),
            "status": self._status_var.get(),
            "tags": self._tags_var.get(),
            "memo": self._memo_text.get("1.0", "end").strip(),
        }

    # Override
    def show_name_error(self, message: Optional[str]) -> None:
        self._name_error_label.config(text=message or "")

    # Override
    def clear_form(self) -> None:
        self._name_var.set("")
        self._assignee_var.set(self.ASSIGNEES[0])
        self._due_date_var.set("")
        self._priority_var.set("中")
        self._status_var.set(self.STATUSES[0])
        self._tags_var.set("")
        self._memo_text.delete("1.0", "end")


class TkSettingsFrame(ttk.Frame, SettingsView):
    """「設定」タブの実装。"""

    ASSIGNEE_OPTIONS = ["指定なし", "佐藤", "田中", "鈴木"]
    DAYS_OPTIONS = ["1", "3", "7"]
    PAGE_SIZE_OPTIONS = ["10", "25", "50"]
    THEME_OPTIONS = ["ライト", "ダーク", "システムに合わせる"]

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, padding=16)
        self._on_field_changed: Optional[Callable[[], None]] = None
        # load_settings() でフォームに値をセットする際、trace経由でon_field_changedが
        # 誤って発火しないようにするためのガード。
        self._loading = False

        self._notify_var = tk.BooleanVar(value=True)
        self._notify_days_var = tk.StringVar(value="3")
        self._default_assignee_var = tk.StringVar(value="指定なし")
        self._page_size_var = tk.StringVar(value="25")
        self._theme_var = tk.StringVar(value="システムに合わせる")

        row = 0
        ttk.Label(self, text="通知", font=("Helvetica", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        row += 1
        ttk.Checkbutton(
            self,
            text="期限が近いタスクを通知する",
            variable=self._notify_var,
            command=self._changed,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
        row += 1
        ttk.Label(self, text="通知するタイミング").grid(row=row, column=0, sticky="w", pady=2)
        ttk.Combobox(
            self,
            textvariable=self._notify_days_var,
            values=self.DAYS_OPTIONS,
            state="readonly",
            width=8,
        ).grid(row=row, column=1, sticky="w", pady=2)
        row += 1

        ttk.Separator(self).grid(row=row, column=0, columnspan=2, sticky="we", pady=10)
        row += 1

        ttk.Label(self, text="既定値", font=("Helvetica", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        row += 1
        ttk.Label(self, text="新規登録時の既定の担当者").grid(row=row, column=0, sticky="w", pady=2)
        ttk.Combobox(
            self,
            textvariable=self._default_assignee_var,
            values=self.ASSIGNEE_OPTIONS,
            state="readonly",
        ).grid(row=row, column=1, sticky="w", pady=2)
        row += 1
        ttk.Label(self, text="一覧の表示件数").grid(row=row, column=0, sticky="w", pady=2)
        ttk.Combobox(
            self,
            textvariable=self._page_size_var,
            values=self.PAGE_SIZE_OPTIONS,
            state="readonly",
            width=8,
        ).grid(row=row, column=1, sticky="w", pady=2)
        row += 1

        ttk.Separator(self).grid(row=row, column=0, columnspan=2, sticky="we", pady=10)
        row += 1

        ttk.Label(self, text="表示・データ", font=("Helvetica", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        row += 1
        ttk.Label(self, text="テーマ").grid(row=row, column=0, sticky="w", pady=2)
        ttk.Combobox(
            self, textvariable=self._theme_var, values=self.THEME_OPTIONS, state="readonly"
        ).grid(row=row, column=1, sticky="w", pady=2)
        row += 1

        data_row = ttk.Frame(self)
        data_row.grid(row=row, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self._export_button = ttk.Button(data_row, text="書き出し")
        self._export_button.pack(side="left", padx=(0, 8))
        self._import_button = ttk.Button(data_row, text="読み込み")
        self._import_button.pack(side="left")
        row += 1

        save_row = ttk.Frame(self)
        save_row.grid(row=row, column=0, columnspan=2, sticky="we", pady=(16, 0))
        self._status_label = ttk.Label(save_row, text="", foreground="#4a6cf7")
        self._status_label.pack(side="left")
        self._save_button = ttk.Button(save_row, text="変更を保存")
        self._save_button.pack(side="right")

        self.columnconfigure(1, weight=1)

        # プルダウン系は値の変更をtraceで検知する（load_settings中は_loadingで抑制）
        for var in (
            self._notify_days_var,
            self._default_assignee_var,
            self._page_size_var,
            self._theme_var,
        ):
            var.trace_add("write", lambda *_: self._changed())

    def _changed(self) -> None:
        if self._loading:
            return
        if self._on_field_changed:
            self._on_field_changed()

    # Override
    def set_on_field_changed(self, handler: Callable[[], None]) -> None:
        self._on_field_changed = handler

    # Override
    def set_on_save_click(self, handler: Callable[[], None]) -> None:
        self._save_button.config(command=handler)

    # Override
    def set_on_export_click(self, handler: Callable[[], None]) -> None:
        self._export_button.config(command=handler)

    # Override
    def set_on_import_click(self, handler: Callable[[], None]) -> None:
        self._import_button.config(command=handler)

    # Override
    def load_settings(self, settings: Settings) -> None:
        self._loading = True
        try:
            self._notify_var.set(settings.notify_enabled)
            self._notify_days_var.set(str(settings.notify_days_before))
            self._default_assignee_var.set(settings.default_assignee)
            self._page_size_var.set(str(settings.page_size))
            self._theme_var.set(settings.theme)
        finally:
            self._loading = False

    # Override
    def get_form_values(self) -> Settings:
        return Settings(
            notify_enabled=self._notify_var.get(),
            notify_days_before=int(self._notify_days_var.get()),
            default_assignee=self._default_assignee_var.get(),
            page_size=int(self._page_size_var.get()),
            theme=self._theme_var.get(),
        )

    # Override
    def set_dirty(self, dirty: bool) -> None:
        self._status_label.config(text="● 未保存の変更があります" if dirty else "")

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


# Called at main.py > def main()
class TkMainWindow:
    """3タブ(タスク一覧/新規登録/設定)をまとめるメインウィンドウ"""

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.title("タスク管理 (MVP)")
        self._root.geometry("640x540")

        notebook = ttk.Notebook(self._root)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.task_list_frame = TkTaskListFrame(notebook)
        self.new_task_frame = TkNewTaskFrame(notebook)
        self.settings_frame = TkSettingsFrame(notebook)

        notebook.add(self.task_list_frame, text="タスク一覧")
        notebook.add(self.new_task_frame, text="新規登録")
        notebook.add(self.settings_frame, text="設定")

    def run(self) -> None:
        self._root.mainloop()
