"""
Backup and generation management for the DB file (app.db)
------------------------------------------------------------
Pure I/O with no dependency on tkinter. The task and settings tables live
together in the same physical file (model.lib.db_path.DEFAULT_DB_PATH), so
backups are handled as a single, file-level mechanism.

SQLite itself, thanks to transactions, is resilient to "corrupted midway
through because of a crash during a write", but it can't protect against
cases where the file itself becomes unreadable, such as disk failure or a
filesystem fault. As a safety net for that, we periodically copy it to a
separate file (called at a fixed interval from the main.py side).

The retention policy is time-based: "keep everything from the last 24
hours." It's time-based rather than count-based (e.g. "last N backups") so
that, even if the DB grows large in the future and the backup interval is
tuned accordingly (e.g. changed from every 15 minutes to every minute), the
requirement "you can go back up to a day" continues to hold without any
code changes.
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
    # If backups happen in quick succession, sub-second clock resolution on
    # some environments can be too coarse for the timestamp alone to be
    # unique (the same name would get overwritten, so no backup is actually
    # gained). Always append a short random suffix to guarantee uniqueness.
    unique_suffix = uuid.uuid4().hex[:8]
    backup_path = backup_dir / f"{source.name}.{timestamp}-{unique_suffix}{_BACKUP_SUFFIX}"
    shutil.copy2(source, backup_path)

    _prune_old_backups(backup_dir, source.name, keep_for)


def _prune_old_backups(backup_dir: Path, db_filename: str, keep_for: timedelta) -> None:
    """Delete backup files older than `keep_for`.
    Age is judged by the file's own modification time (mtime) — simpler than
    parsing the timestamp out of the filename, and won't break if the naming
    convention changes in the future.
    """
    pattern = f"{db_filename}.*{_BACKUP_SUFFIX}"
    cutoff = datetime.now() - keep_for
    for backup_file in backup_dir.glob(pattern):
        backup_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
        if backup_time < cutoff:
            backup_file.unlink()
