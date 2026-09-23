"""
Model — app settings (dataclass)
-----------------------------------
Holds settings values only; SettingsModel handles persistence.
"""

from dataclasses import dataclass


@dataclass
class Settings:
    notify_enabled: bool = True
    notify_days_before: int = 3
    backup_interval_minutes: int = 15
