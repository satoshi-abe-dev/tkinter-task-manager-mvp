"""
Model — 設定の永続化(SQLite)
------------------------------
設定をSQLiteに保存・読み込みする、tkinterに依存しない純粋なI/Oロジック。
Settingsデータクラス(settings_model.py)には依存せず、プリミティブな値だけを
やり取りする（settings_model.pyとの循環importを避けるため）。
"""

import sqlite3
from pathlib import Path
from typing import Tuple

from Model.db_path import DEFAULT_DB_PATH

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    notify_enabled INTEGER NOT NULL,
    notify_days_before INTEGER NOT NULL,
    backup_interval_minutes INTEGER NOT NULL
)
"""

# settingsは常に1行だけ(id=1)を使い回す単一行テーブル。
_DEFAULT_NOTIFY_ENABLED = True
_DEFAULT_NOTIFY_DAYS_BEFORE = 3
_DEFAULT_BACKUP_INTERVAL_MINUTES = 15


def connect(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """DBファイルへ接続する。ファイル・テーブルが無ければ作成する。
    db_path=":memory:" を渡すとテスト用の使い捨てDBになる。
    """
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(_CREATE_TABLE_SQL)
    conn.commit()
    return conn


def load(conn: sqlite3.Connection) -> Tuple[bool, int, int]:
    """設定を読み込む。行がまだ無ければ既定値で1行作ってから返す（初回起動時）。
    戻り値: (notify_enabled, notify_days_before, backup_interval_minutes)
    """
    row = conn.execute(
        "SELECT notify_enabled, notify_days_before, backup_interval_minutes "
        "FROM settings WHERE id = 1"
    ).fetchone()
    if row is None:
        save(
            conn,
            _DEFAULT_NOTIFY_ENABLED,
            _DEFAULT_NOTIFY_DAYS_BEFORE,
            _DEFAULT_BACKUP_INTERVAL_MINUTES,
        )
        return (
            _DEFAULT_NOTIFY_ENABLED,
            _DEFAULT_NOTIFY_DAYS_BEFORE,
            _DEFAULT_BACKUP_INTERVAL_MINUTES,
        )
    return bool(row[0]), int(row[1]), int(row[2])


def save(
    conn: sqlite3.Connection,
    notify_enabled: bool,
    notify_days_before: int,
    backup_interval_minutes: int,
) -> None:
    """設定を保存する（1行しか無いのでINSERT OR REPLACEで丸ごと置き換える）"""
    conn.execute(
        "INSERT OR REPLACE INTO settings "
        "(id, notify_enabled, notify_days_before, backup_interval_minutes) VALUES (1, ?, ?, ?)",
        (int(notify_enabled), notify_days_before, backup_interval_minutes),
    )
    conn.commit()
