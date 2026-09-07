"""
View（Tkinter実装層）— タスク一覧タブ
--------------------------------------
view/task/contract.py の抽象クラス TaskListView を、Tkinterを使って具体的に実装する。
Tkinterへの依存はこのファイル（および同じ役割の view/settings/tk_frame.py）だけに
閉じ込める。
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


# Called at view/tk_main_window.py > class TkMainWindow
# 継承順: 具象ウィジェット(ttk.Frame) → mixin(コールバック機構) → 契約(ABC)
class TkTaskListFrame(ttk.Frame, CallbackRegistryMixin, TaskListView):
    """「タスク一覧」タブの実装。ttk.Treeviewで表形式に表示する。

    セルをダブルクリックするとインライン編集ができる。編集内容の確定は
    Presenterに委ねる（Viewはここで直接Modelを書き換えない）。
    表の下の「追加」「削除」ボタンで、タスクの追加・削除を行う。
    """

    PRIORITIES = PRIORITIES
    STATUSES = STATUSES

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, padding=16)
        # コールバック(_on_cell_edited など)は CallbackRegistryMixin が名前付きで
        # 保持する。ここで個別に None 初期化する必要はない。
        self._editor: Optional[tk.Widget] = None
        self._date_picker: Optional[tk.Toplevel] = None

        # 既定の行高(18px前後)だとインライン編集用のEntry/Comboboxを重ねた時に
        # 上下が窮屈になり文字が見切れるため、この一覧専用のスタイルで広げる。
        style = ttk.Style(self)
        style.configure("TaskList.Treeview", rowheight=28)

        # このフレーム自身のgrid構成: 行0(表+スクロールバー)が余白を吸収し、
        # 行1(追加/削除ボタン)・行2(書き出し/読み込みボタン)は内容ぶんの
        # 高さで下端に固定される。
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)

        # 表とスクロールバーをまとめる専用フレーム。
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)  # 表側の列が余白を吸収
        tree_frame.columnconfigure(1, weight=0)  # スクロールバー側は内容幅のまま
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

        # 期限が近い/過ぎているタスクの行ハイライト用タグ。
        # ttk.Labelの背景色指定はAquaで無視されることがあるが、Treeviewの行タグは
        # 別の描画経路のため背景色が確実に反映される。
        self._tree.tag_configure("warning", background="#fbeed7", foreground="#b8790f")
        self._tree.tag_configure("overdue", background="#fbe4e4", foreground="#d94f4f")

        self._tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 「追加」「削除」ボタンは、隣接させて表の幅いっぱいに広げる
        # (両列をweight=1にして幅を均等に分配)。
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

        # CSV書き出し/読み込みは「追加」ボタンの下に配置する（左詰め、幅は
        # 「追加」ボタンに揃えず内容ぶんのみ）。
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
        # ttk.Treeviewは既定(selectmode="extended")で複数選択に対応しており、
        # Shift/Cmdクリックで選択した行はすべてselection()に含まれる。
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
        # 行の無い領域（表の下の余白など）をクリックした時は選択を解除する。
        # ヘッダー部分("heading")はソート用クリックなので対象外。
        if self._tree.identify_region(event.x, event.y) == "nothing":
            self._tree.selection_remove(*self._tree.selection())

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

        # 期限欄だけは、セルに重ねるのではなく別ウィンドウのカレンダーで選ばせる。
        # tkcalendar.DateEntryは装飾なしウィンドウ(overrideredirect)にカレンダーを
        # 描画するが、macOSのAqua環境ではその中のttkウィジェットの文字色が正しく
        # 描画されないことがある。装飾ありの通常のToplevelにCalendarを直接
        # 埋め込むことで、この描画崩れと内部の後処理順序に起因するエラーの両方を避ける。
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

        # 編集ウィジェットをセルの矩形ぴったりに重ねると、ウィジェット自体の
        # フォーカスハイライト枠が内側の文字表示領域を圧迫し、テキストが
        # 見切れてしまう。枠の分だけ少し大きめ・上方向にずらして配置する。
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
        # 既に開いている日付ピッカーがあれば、重ねて表示せず先に閉じる
        # （前のポップアップを残したまま新しいものを開くと、ウィンドウが重なって
        # 数字が崩れて見えることがある）。
        self._destroy_editor()

        popup = tk.Toplevel(self)
        self._date_picker = popup
        popup.bind(
            "<Destroy>",
            lambda e: setattr(self, "_date_picker", None) if e.widget is popup else None,
        )
        popup.title("Select Due Date")
        popup.transient(self.winfo_toplevel())
        popup.resizable(False, False)

        calendar_kwargs = {
            "selectmode": "day",
            "date_pattern": _DATE_PATTERN,
            # 月名・曜日名をGUIの言語(英語)に合わせる
            "locale": "en_US",
            # 週番号列は使わないので非表示（先頭列に出る紛らわしい数字の正体はこれ）。
            "showweeknumbers": False,
            # macOSのAquaテーマはttkカスタムスタイル(TLabel)の背景色指定を無視するため、
            # tkcalendarが標準で使う「白文字」がその場合は常に白背景の上に乗って
            # 見えなくなる（月/年ヘッダーがこれで消えていた）。文字色を黒に統一する。
            "foreground": "black",
            # 選択中の日のハイライトも同じ理由でselectbackgroundが効かず、背景色では
            # 目立たせられない。文字色を変えて目立たせる（フォントの太字化は下で追加）。
            "selectforeground": "#d94f4f",
            # 一方でTButton(月/年の矢印ボタン)の背景色はAquaでも反映されるため、
            # 既定の濃いグレー(gray30)のままだと黒い矢印との見分けがつきにくい。
            # 明るい背景にして矢印が見えるようにする。
            "background": "white",
        }
        initial = None
        try:
            initial = datetime.strptime(current_value, "%Y-%m-%d").date()
            calendar_kwargs.update(year=initial.year, month=initial.month, day=initial.day)
        except ValueError:
            pass  # 既存の値が日付として解釈できない場合は今日の月をそのまま表示

        popup.columnconfigure(0, weight=1)

        # 現在設定されている期限を常に文字で表示しておく。カレンダー側のハイライトは
        # 開いた直後の月にしか出ないため、月を送って見えなくなっても分かるようにする。
        info_row = ttk.Frame(popup)
        info_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        info_row.columnconfigure(0, weight=1)  # ラベル側が伸び、戻るボタンは右端に寄る
        info_label = ttk.Label(info_row, text=f"Current due date: {current_value or 'Not set'}")
        info_label.grid(row=0, column=0, sticky="w")

        calendar = Calendar(popup, **calendar_kwargs)
        calendar.grid(row=1, column=0, padx=10, pady=10)
        # selectbackground(背景の塗りつぶし)やborderwidth/relief(枠線)は、Aquaでは
        # ttkカスタムスタイルとして値をセットしても描画に反映されない。確実に効く
        # 「文字色」「太さ」「大きさ」だけで選択中の日を強調する。
        # tkcalendarはスタイル名ごとのフォント上書きを構築時引数として公開していない
        # ため、生成後にスタイルを直接書き換える。
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

        # ジオメトリ(位置)を計算する前に、ウィジェットの実サイズを確定させておく
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
