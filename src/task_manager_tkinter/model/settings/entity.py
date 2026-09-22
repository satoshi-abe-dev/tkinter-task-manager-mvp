"""
Model — app settings (dataclass)
-----------------------------------
Represents the values for one set of settings. Holds no logic — persistence
and retrieval are handled by SettingsModel.
"""

from dataclasses import dataclass


@dataclass
class Settings:
    notify_enabled: bool = True
    notify_days_before: int = 3
    backup_interval_minutes: int = 15
