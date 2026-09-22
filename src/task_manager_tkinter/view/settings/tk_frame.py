"""
View (Tkinter implementation layer) — settings tab
------------------------------------------------------
Provides a concrete Tkinter implementation of the abstract class
SettingsView from view/settings/contract.py. The dependency on Tkinter is
confined to this file (and view/task/tk_frame.py, which plays the same role).
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Callable

from task_manager_tkinter.model.settings import Settings
from task_manager_tkinter.view.callbacks import CallbackRegistryMixin
from task_manager_tkinter.view.settings.contract import SettingsView


# Inheritance order: concrete widget (ttk.Frame) -> mixin (callback machinery) -> contract (ABC)
class TkSettingsFrame(ttk.Frame, CallbackRegistryMixin, SettingsView):
    """Implementation of the "Settings" tab."""

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, padding=16)
        # Callbacks (_on_field_changed / _on_highlight_toggled) are held by
        # name by CallbackRegistryMixin.
        # Guard against field_changed firing accidentally via a variable
        # trace while load_settings() is setting values on the form.
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
        # Align the start of the next row with where the "text" of the
        # checkbutton above it begins. A checkbutton's text is pushed right
        # by its check indicator, so measure that indent and use it as padx.
        days_row.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=2,
            padx=(self._measure_checkbox_text_indent(notify_checkbox), 0),
        )
        # Only allow typing non-negative integers directly (reject negative numbers/letters).
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
        # Spell out the unit (days) explicitly
        self._days_unit_label = ttk.Label(days_row, text="days before due date")
        self._days_unit_label.grid(row=0, column=1, padx=(6, 0))
        row += 1

        ttk.Label(self, text="Backup", font=("Helvetica", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(16, 4)
        )
        row += 1
        backup_row = ttk.Frame(self)
        backup_row.grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
        # Only allow typing non-negative integers directly (same validation as the days field).
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

        # Detect changes to the days field / backup interval field via a trace
        # (suppressed by _loading while load_settings runs).
        self._notify_days_var.trace_add("write", lambda *_: self._changed())
        self._backup_interval_var.trace_add("write", lambda *_: self._changed())

        # Match the days field's state to the checkbutton's initial state (on by default)
        self._update_days_row_state()

    def _changed(self) -> None:
        if self._loading:
            return
        self._fire("field_changed")

    def _on_notify_toggled(self) -> None:
        self._update_days_row_state()
        # Highlight on/off is applied to the list tab immediately
        self._fire("highlight_toggled", self._notify_var.get())

    def _update_days_row_state(self) -> None:
        """Gray out and disable editing of the days field while the checkbutton is OFF"""
        state = ["!disabled"] if self._notify_var.get() else ["disabled"]
        self._days_spinbox.state(state)
        self._days_unit_label.state(state)

    def _measure_checkbox_text_indent(self, checkbutton: ttk.Checkbutton) -> int:
        """Measure, in pixels, where a Checkbutton's "text" actually begins (distance from the left edge).

        Subtracting the width of the text itself from the widget's total
        width gives the amount taken up by the check indicator plus padding,
        which is exactly where the text starts.
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
        """Restrict input in the days field / backup interval field to
        non-negative integers (or a blank value mid-edit) only
        """
        return proposed == "" or proposed.isdigit()

    # Override
    def set_on_field_changed(self, handler: Callable[[], None]) -> None:
        self._set_callback("field_changed", handler)

    # Override
    def set_on_highlight_toggled(self, handler: Callable[[bool], None]) -> None:
        self._set_callback("highlight_toggled", handler)

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
