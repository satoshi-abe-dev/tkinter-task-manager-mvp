"""
Backup and generation management for the DB file (app.db)
------------------------------------------------------------
Pure I/O, no tkinter. Tasks and settings share one physical file
(model.lib.db_path.DEFAULT_DB_PATH), so backups work at the file level.

SQLite's transactions survive a crash mid-write, but not disk failure or
filesystem corruption — this periodic copy (called from main.py) is the
safety net for that.

Retention is time-based ("last 24 hours"), not count-based, so tuning the
backup interval later doesn't silently shrink the retained history.
"""

import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path

_BACKUP_SUFFIX = ".bak"
_TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"
_DEFAULT_RETENTION = timedelta(hours=24)


def backup_and_rotate(db_path: str, keep_for: timedelta = _DEFAULT_RETENTION) -> None:
    """Back up the current contents of db_path with a timestamp, and delete
    any backups older than `keep_for`.

    Does nothing when db_path == ":memory:" or the DB file doesn't exist yet
    (e.g. on first launch, before save() has ever been called).
    """
    source = Path(db_path)
    if db_path == ":memory:" or not source.exists():
        return

    backup_dir = source.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime(_TIMESTAMP_FORMAT)
    # Sub-second clock resolution can collide on rapid backups; add a random suffix
    unique_suffix = uuid.uuid4().hex[:8]
    backup_path = backup_dir / f"{source.name}.{timestamp}-{unique_suffix}{_BACKUP_SUFFIX}"
    shutil.copy2(source, backup_path)

    _prune_old_backups(backup_dir, source.name, keep_for)


def _prune_old_backups(backup_dir: Path, db_filename: str, keep_for: timedelta) -> None:
    """Delete backup files older than `keep_for`, judged by mtime (simpler
    than parsing the timestamp out of the filename)."""
    pattern = f"{db_filename}.*{_BACKUP_SUFFIX}"
    cutoff = datetime.now() - keep_for
    for backup_file in backup_dir.glob(pattern):
        backup_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
        if backup_time < cutoff:
            backup_file.unlink()
