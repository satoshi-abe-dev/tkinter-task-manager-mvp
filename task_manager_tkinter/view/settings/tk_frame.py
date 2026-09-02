"""
View（Tkinter実装層）— 設定タブ
--------------------------------
view/settings/contract.py の抽象クラス SettingsView を、Tkinterを使って具体的に実装する。
Tkinterへの依存はこのファイル（および同じ役割の view/task/tk_frame.py）だけに
閉じ込める。
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Callable, Optional

from task_manager_tkinter.model.settings import Settings
from task_manager_tkinter.view.settings.contract import SettingsView


class TkSettingsFrame(ttk.Frame, SettingsView):
    """「設定」タブの実装。"""

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, padding=16)
        self._on_field_changed: Optional[Callable[[], None]] = None
        self._on_highlight_toggled: Optional[Callable[[bool], None]] = None
        # load_settings() でフォームに値をセットする際、trace経由でon_field_changedが
        # 誤って発火しないようにするためのガード。
        self._loading = False

        self._notify_var = tk.BooleanVar(value=True)
        self._notify_days_var = tk.StringVar(value="3")
        self._backup_interval_var = tk.StringVar(value="15")

        row = 0
        ttk.Label(self, text="Due Date Highlight", font=("Helvetica", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        row += 1
        notify_checkbox = ttk.Checkbutton(
            self,
            text="Highlight upcoming incomplete tasks",
            variable=self._notify_var,
            command=self._on_notify_toggled,
        )
        notify_checkbox.grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
        row += 1
        days_row = ttk.Frame(self)
        # 次の行の先頭を、直前のチェックボタンの「文字列」の開始位置に揃える。
        # チェックボタンはチェック用のインジケーター分だけ文字列が右にずれるため、
        # そのインデント幅を実測してpadxに使う。
        days_row.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=2,
            padx=(self._measure_checkbox_text_indent(notify_checkbox), 0),
        )
        # 0以上の整数のみを直接入力できるようにする(負の数・文字は弾く)。
        validate_digits = (self.register(self._validate_day_count), "%P")
        self._days_spinbox = ttk.Spinbox(
            days_row,
            from_=0,
            to=365,
            increment=1,
            textvariable=self._notify_days_var,
            width=5,
            validate="key",
            validatecommand=validate_digits,
        )
        self._days_spinbox.grid(row=0, column=0)
        # 単位(日)を明示する
        self._days_unit_label = ttk.Label(days_row, text="days before due date")
        self._days_unit_label.grid(row=0, column=1, padx=(6, 0))
        row += 1

        ttk.Label(self, text="Backup", font=("Helvetica", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(16, 4)
        )
        row += 1
        backup_row = ttk.Frame(self)
        backup_row.grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
        # 0以上の整数のみを直接入力できるようにする（日数欄と同じバリデーション）。
        validate_digits = (self.register(self._validate_day_count), "%P")
        self._backup_interval_spinbox = ttk.Spinbox(
            backup_row,
            from_=1,
            to=1440,
            increment=1,
            textvariable=self._backup_interval_var,
            width=5,
            validate="key",
            validatecommand=validate_digits,
        )
        self._backup_interval_spinbox.grid(row=0, column=0)
        ttk.Label(backup_row, text="minutes between automatic backups").grid(
            row=0, column=1, padx=(6, 0)
        )
        row += 1

        self.columnconfigure(1, weight=1)

        # 日数欄・バックアップ間隔欄の値変更をtraceで検知する
        # （load_settings中は_loadingで抑制）
        self._notify_days_var.trace_add("write", lambda *_: self._changed())
        self._backup_interval_var.trace_add("write", lambda *_: self._changed())

        # チェックボタンの初期状態(既定でON)に日数欄を合わせる
        self._update_days_row_state()

    def _changed(self) -> None:
        if self._loading:
            return
        if self._on_field_changed:
            self._on_field_changed()

    def _on_notify_toggled(self) -> None:
        self._update_days_row_state()
        # ハイライトON/OFFは一覧タブへ即座に反映する
        if self._on_highlight_toggled:
            self._on_highlight_toggled(self._notify_var.get())

    def _update_days_row_state(self) -> None:
        """チェックボタンがOFFの間、日数欄をグレーアウトして編集できなくする"""
        state = ["!disabled"] if self._notify_var.get() else ["disabled"]
        self._days_spinbox.state(state)
        self._days_unit_label.state(state)

    def _measure_checkbox_text_indent(self, checkbutton: ttk.Checkbutton) -> int:
        """Checkbuttonの「文字列」が実際に始まる位置(左端からの距離)をpx単位で測る。

        チェック用のインジケーター＋余白の分だけ、ウィジェット全体の幅から
        文字列そのものの幅を引けば、文字列の開始位置が求まる。
        """
        self.update_idletasks()
        style_name = checkbutton.cget("style") or "TCheckbutton"
        style = ttk.Style(self)
        font_name = style.lookup(style_name, "font") or "TkDefaultFont"
        font = tkfont.Font(font=font_name)
        text_width = font.measure(checkbutton.cget("text"))
        return max(checkbutton.winfo_reqwidth() - text_width, 0)

    @staticmethod
    def _validate_day_count(proposed: str) -> bool:
        """日数欄・バックアップ間隔欄への入力を0以上の整数
        （または編集途中の空欄）だけに制限する
        """
        return proposed == "" or proposed.isdigit()

    # Override
    def set_on_field_changed(self, handler: Callable[[], None]) -> None:
        self._on_field_changed = handler

    # Override
    def set_on_highlight_toggled(self, handler: Callable[[bool], None]) -> None:
        self._on_highlight_toggled = handler

    # Override
    def load_settings(self, settings: Settings) -> None:
        self._loading = True
        try:
            self._notify_var.set(settings.notify_enabled)
            self._notify_days_var.set(str(settings.notify_days_before))
            self._backup_interval_var.set(str(settings.backup_interval_minutes))
        finally:
            self._loading = False
        self._update_days_row_state()

    # Override
    def get_form_values(self) -> Settings:
        return Settings(
            notify_enabled=self._notify_var.get(),
            notify_days_before=int(self._notify_days_var.get()),
            backup_interval_minutes=int(self._backup_interval_var.get()),
        )
