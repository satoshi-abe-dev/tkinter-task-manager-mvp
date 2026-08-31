"""
DBファイル(app.db)のバックアップ・世代管理
--------------------------------------------
tkinterに依存しない純粋なI/O。タスク用・設定用のテーブルは同じ物理ファイル
(db_path.DEFAULT_DB_PATH)に同居しているため、バックアップはファイル単位で
1つの仕組みにまとめている。

SQLite自体はトランザクションのおかげで「書き込み中のクラッシュで中途半端に
壊れる」ことには強いが、ディスク故障やファイルシステムの異常など、
ファイルそのものが読めなくなるケースまでは守れない。そのための保険として、
Save操作のたびに別ファイルへコピーしておく。バックアップを無制限に増やすと
ディスクを圧迫するため、直近N件だけを残して古いものから削除する
（世代管理）。
"""

import shutil
import uuid
from datetime import datetime
from pathlib import Path

_BACKUP_SUFFIX = ".bak"
_TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"
_DEFAULT_KEEP = 10


def backup_and_rotate(db_path: str, keep: int = _DEFAULT_KEEP) -> None:
    """db_pathの現在の内容をタイムスタンプ付きでバックアップし、
    古いバックアップを残り`keep`件だけになるよう削除する。

    db_path=":memory:"の場合や、DBファイルがまだ存在しない場合（初回起動で
    一度もsave()していない等）は何もしない。
    """
    source = Path(db_path)
    if db_path == ":memory:" or not source.exists():
        return

    backup_dir = source.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime(_TIMESTAMP_FORMAT)
    # 短時間に連続でSaveされると、環境によっては秒未満の時計の分解能が粗く
    # timestampだけでは衝突しうる（同じ名前で上書きされ、実質バックアップが
    # 増えない）。一意性を保証するため、短いランダムな符号を必ず付ける。
    unique_suffix = uuid.uuid4().hex[:8]
    backup_path = backup_dir / f"{source.name}.{timestamp}-{unique_suffix}{_BACKUP_SUFFIX}"
    shutil.copy2(source, backup_path)

    _prune_old_backups(backup_dir, source.name, keep)


def _prune_old_backups(backup_dir: Path, db_filename: str, keep: int) -> None:
    """バックアップファイル名にタイムスタンプが含まれているため、ファイル名の
    文字列順ソートがそのまま古い順になる。それを利用して、超過分のうち
    最も古いものから削除する。
    """
    pattern = f"{db_filename}.*{_BACKUP_SUFFIX}"
    backups = sorted(backup_dir.glob(pattern))
    excess = len(backups) - keep
    if excess <= 0:
        # backups[:excess]は、excessが負でも「末尾からexcess件を除く」という
        # 意味になってしまい(例: backups[:-1]は最後の1件を除いた全部)、
        # 超過が無い場合に誤って削除してしまう。超過が無ければ何もしない。
        return
    for old_backup in backups[:excess]:
        old_backup.unlink()
