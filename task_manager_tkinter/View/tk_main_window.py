"""
View（Tkinter実装層）
---------------------
task_list_view / settings_view の2つの抽象クラスを、
Tkinterを使って具体的に実装する層。Tkinterへの依存はこのファイルだけに閉じ込める。

タブ1枚 = 1つのフレームクラスとして実装し、それぞれ対応する抽象Viewを継承する。
TkMainWindowはそれらをttk.Notebookにまとめ、ウィンドウ全体の起動(run)を担う。
"""

import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import Callable, List, Optional

from tkcalendar import Calendar

from Model.settings_model import Settings
from Model.task import PRIORITIES, STATUSES, Task
from View.settings_view import SettingsView
from View.task_list_view import TaskListView

_DATE_PATTERN = "yyyy-mm-dd"

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
    表の下の「追加」「削除」ボタンで、タスクの追加・削除を行う。
    """

    PRIORITIES = PRIORITIES
    STATUSES = STATUSES

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, padding=16)
        self._on_cell_edited: Optional[Callable[[int, str, str], None]] = None
        self._on_column_clicked: Optional[Callable[[str], None]] = None
        self._on_add_click: Optional[Callable[[], None]] = None
        self._on_delete_click: Optional[Callable[[int], None]] = None
        self._editor: Optional[tk.Widget] = None
        self._date_picker: Optional[tk.Toplevel] = None

        # 既定の行高(18px前後)だとインライン編集用のEntry/Comboboxを重ねた時に
        # 上下が窮屈になり文字が見切れるため、この一覧専用のスタイルで広げる。
        style = ttk.Style(self)
        style.configure("TaskList.Treeview", rowheight=28)

        # 「追加」「削除」ボタンは、隣接させて表の幅いっぱいに広げる
        # (fill="x", expand=Trueで2つのボタンに幅を均等に分配)。
        # 表より先にpack(side="bottom")しておくことで、下端に固定される。
        button_row = ttk.Frame(self)
        self._add_button = ttk.Button(
            button_row, text="＋ 追加", command=self._handle_add_click
        )
        self._add_button.pack(side="left", fill="x", expand=True)
        self._delete_button = ttk.Button(
            button_row, text="－ 削除", command=self._handle_delete_click, state="disabled"
        )
        self._delete_button.pack(side="left", fill="x", expand=True)
        button_row.pack(side="bottom", fill="x", pady=(8, 0))

        # 表とスクロールバーをまとめる専用フレーム。ボタン行(下端固定)を差し引いた
        # 残りのスペースいっぱいに広がる。
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

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

        self._tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<Button-1>", self._on_click)
        self._tree.bind("<<TreeviewSelect>>", self._on_selection_changed)

    def _make_heading_handler(self, field: str) -> Callable[[], None]:
        def handler() -> None:
            if self._on_column_clicked:
                self._on_column_clicked(field)

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
        self._on_cell_edited = handler

    # Override
    def set_on_column_clicked(self, handler: Callable[[str], None]) -> None:
        self._on_column_clicked = handler

    # Override
    def show_sort_state(self, field: Optional[str], ascending: bool) -> None:
        for col in _COLUMNS:
            text = _COLUMN_LABELS[col]
            if col == field:
                text += " ▲" if ascending else " ▼"
            self._tree.heading(col, text=text)

    # Override
    def set_on_add_click(self, handler: Callable[[], None]) -> None:
        self._on_add_click = handler

    # Override
    def set_on_delete_click(self, handler: Callable[[int], None]) -> None:
        self._on_delete_click = handler

    # Override
    def select_task(self, task_id: int) -> None:
        iid = str(task_id)
        if self._tree.exists(iid):
            self._tree.selection_set(iid)
            self._tree.see(iid)
            self._tree.focus(iid)

    def _on_selection_changed(self, event: tk.Event) -> None:
        state = "normal" if self._tree.selection() else "disabled"
        self._delete_button.config(state=state)

    def _handle_add_click(self) -> None:
        if self._on_add_click:
            self._on_add_click()

    def _handle_delete_click(self) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        row_id = selection[0]
        task_id = int(row_id)
        name = self._tree.set(row_id, "name")

        confirmed = messagebox.askyesno(
            "確認",
            f"「{name}」を削除しますか？\nこの操作は取り消せません。",
        )
        if confirmed and self._on_delete_click:
            self._on_delete_click(task_id)

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
            if new_value != current_value and self._on_cell_edited:
                self._on_cell_edited(task_id, field, new_value)

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
        popup.title("期限を選択")
        popup.transient(self.winfo_toplevel())
        popup.resizable(False, False)

        calendar_kwargs = {
            "selectmode": "day",
            "date_pattern": _DATE_PATTERN,
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

        # 現在設定されている期限を常に文字で表示しておく。カレンダー側のハイライトは
        # 開いた直後の月にしか出ないため、月を送って見えなくなっても分かるようにする。
        info_row = ttk.Frame(popup)
        info_row.pack(fill="x", padx=10, pady=(10, 0))
        ttk.Label(info_row, text=f"現在の期限: {current_value or '未設定'}").pack(side="left")

        calendar = Calendar(popup, **calendar_kwargs)
        calendar.pack(padx=10, pady=10)
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
                text="この日に戻る",
                command=lambda: calendar.selection_set(initial),
            )
            back_button.pack(side="right")

        # ジオメトリ(位置)を計算する前に、ウィジェットの実サイズを確定させておく
        popup.update_idletasks()

        def on_selected(_event: Optional[tk.Event] = None) -> None:
            new_value = calendar.get_date()
            popup.destroy()
            if new_value != current_value and self._on_cell_edited:
                self._on_cell_edited(task_id, "due_date", new_value)

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


class TkSettingsFrame(ttk.Frame, SettingsView):
    """「設定」タブの実装。"""

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
            self._page_size_var.set(str(settings.page_size))
            self._theme_var.set(settings.theme)
        finally:
            self._loading = False

    # Override
    def get_form_values(self) -> Settings:
        return Settings(
            notify_enabled=self._notify_var.get(),
            notify_days_before=int(self._notify_days_var.get()),
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
    """2タブ(タスク一覧/設定)をまとめるメインウィンドウ"""

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.title("タスク管理")
        self._root.geometry("640x540")

        notebook = ttk.Notebook(self._root)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.task_list_frame = TkTaskListFrame(notebook)
        self.settings_frame = TkSettingsFrame(notebook)

        notebook.add(self.task_list_frame, text="タスク一覧")
        notebook.add(self.settings_frame, text="設定")

    def run(self) -> None:
        self._root.mainloop()
