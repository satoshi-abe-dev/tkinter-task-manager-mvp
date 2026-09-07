"""
Model — アプリ設定（データクラス）
----------------------------------
設定1件分の値を表す。ロジックは持たない。永続化・取得は SettingsModel が担う。
"""

from dataclasses import dataclass


@dataclass
class Settings:
    notify_enabled: bool = True
    notify_days_before: int = 3
    backup_interval_minutes: int = 15
