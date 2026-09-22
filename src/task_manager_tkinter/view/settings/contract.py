"""
View (abstract layer) — settings tab
---------------------------------------
Defines only the "contract" the Presenter depends on.
"""

from abc import ABC, abstractmethod
from typing import Callable

from task_manager_tkinter.model.settings import Settings


class SettingsView(ABC):
    @abstractmethod
    def set_on_field_changed(self, handler: Callable[[], None]) -> None:
        """Register a handler called whenever any settings field changes (so it can be saved immediately)"""

    @abstractmethod
    def set_on_highlight_toggled(self, handler: Callable[[bool], None]) -> None:
        """Register a handler called when the highlight on/off checkbox changes.
        Used to apply it to the list tab's highlighting immediately.
        """

    @abstractmethod
    def load_settings(self, settings: Settings) -> None:
        """Apply the given settings values to the form (used at startup, right after saving, etc.)"""

    @abstractmethod
    def get_form_values(self) -> Settings:
        """Return the form's current input as a Settings"""
