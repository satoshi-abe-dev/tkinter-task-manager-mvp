"""
DBファイル(app.db)のバックアップ・世代管理
--------------------------------------------
tkinterに依存しない純粋なI/O。タスク用・設定用のテーブルは同じ物理ファイル
(model.lib.db_path.DEFAULT_DB_PATH)に同居しているため、バックアップはファイル単位で
1つの仕組みにまとめている。

SQLite自体はトランザクションのおかげで「書き込み中のクラッシュで中途半端に
壊れる」ことには強いが、ディスク故障やファイルシステムの異常など、
ファイルそのものが読めなくなるケースまでは守れない。そのための保険として、
定期的に別ファイルへコピーしておく（main.py側で一定間隔ごとに呼ばれる）。

保持方針は「直近24時間以内のものは全部残す」という時間ベース。件数ベース
（直近N件）ではなく時間ベースにしているのは、将来DBが大規模化してバックアップ
間隔を調整しても（例: 15分おき→1分おきに変更）、コードを直さずに「1日分は
遡れる」という要件がそのまま保たれるようにするため。
"""

import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path

_BACKUP_SUFFIX = ".bak"
_TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"
_DEFAULT_RETENTION = timedelta(hours=24)


def backup_and_rotate(db_path: str, keep_for: timedelta = _DEFAULT_RETENTION) -> None:
    """db_pathの現在の内容をタイムスタンプ付きでバックアップし、
    `keep_for`より古いバックアップを削除する。

    db_path=":memory:"の場合や、DBファイルがまだ存在しない場合（初回起動で
    一度もsave()していない等）は何もしない。
    """
    source = Path(db_path)
    if db_path == ":memory:" or not source.exists():
        return

    backup_dir = source.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime(_TIMESTAMP_FORMAT)
    # 短時間に連続でバックアップされると、環境によっては秒未満の時計の分解能が
    # 粗くtimestampだけでは衝突しうる（同じ名前で上書きされ、実質バックアップが
    # 増えない）。一意性を保証するため、短いランダムな符号を必ず付ける。
    unique_suffix = uuid.uuid4().hex[:8]
    backup_path = backup_dir / f"{source.name}.{timestamp}-{unique_suffix}{_BACKUP_SUFFIX}"
    shutil.copy2(source, backup_path)

    _prune_old_backups(backup_dir, source.name, keep_for)


def _prune_old_backups(backup_dir: Path, db_filename: str, keep_for: timedelta) -> None:
    """`keep_for`より古いバックアップファイルを削除する。
    ファイル自体の更新日時(mtime)で古さを判定する（ファイル名のタイムスタンプを
    パースするより単純で、命名規則が将来変わっても壊れない）。
    """
    pattern = f"{db_filename}.*{_BACKUP_SUFFIX}"
    cutoff = datetime.now() - keep_for
    for backup_file in backup_dir.glob(pattern):
        backup_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
        if backup_time < cutoff:
            backup_file.unlink()
