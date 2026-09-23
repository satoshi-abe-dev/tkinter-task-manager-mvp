"""
Presenter — settings tab
-------------------------
Loads/saves settings, writing to the DB on every field change (Auto Save).
CSV export/import is task data, so it lives on TaskListPresenter instead.
"""

from typing import Callable

from task_manager_tkinter.model.settings import SettingsModel
from task_manager_tkinter.view.settings import SettingsView


class SettingsPresenter:
    def __init__(
        self,
        settings_model: SettingsModel,
        view: SettingsView,
        on_settings_saved: Callable[[], None],
    ) -> None:
        self.settings_model = settings_model
        self.view = view
        self.on_settings_saved = on_settings_saved

        self.view.load_settings(self.settings_model.get())
        self.view.set_on_field_changed(self.on_field_changed)
        self.view.set_on_highlight_toggled(self.on_highlight_toggled)

    def on_field_changed(self) -> None:
        """Called whenever any settings field changes. Saves immediately"""
        self._save_now()

    def on_highlight_toggled(self, enabled: bool) -> None:
        """Applies the highlight on/off toggle to the list tab immediately"""
        self.settings_model.set_notify_enabled(enabled)
        self.on_settings_saved()

    def _save_now(self) -> None:
        """Save the View form's current values to the DB as-is"""
        settings = self.view.get_form_values()
        self.settings_model.update(settings)
        # Notification settings drive the list tab's due-date highlight
        self.on_settings_saved()
