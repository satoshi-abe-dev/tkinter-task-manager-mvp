"""
Presenter — settings tab
-------------------------
Handles loading and saving settings. Saves to the DB immediately whenever a
field changes (Auto Save). CSV export/import operates on task data, which
is conceptually different from settings, so it belongs to the task list tab
side (TaskListPresenter) instead.
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
        """Called when the highlight on/off checkbox is toggled.
        Applies the change to the list tab's highlighting immediately.
        """
        self.settings_model.set_notify_enabled(enabled)
        self.on_settings_saved()

    def _save_now(self) -> None:
        """Save the View form's current values to the DB as-is"""
        settings = self.view.get_form_values()
        self.settings_model.update(settings)
        # The notification settings (enabled/disabled, how many days ahead)
        # are used by the list tab's due-date highlighting, so trigger a
        # re-evaluation there right after saving.
        self.on_settings_saved()
