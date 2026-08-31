"""
Model — タスクの永続化(SQLite)
--------------------------------
タスクをSQLiteに保存・読み込みする、tkinterに依存しない純粋なI/Oロジック。
csv_io.pyと同じ位置づけで、TaskModelがこのモジュールを介してDBを読み書きする。
Presenter/Viewは永続化の仕組み（ここがSQLiteであること）を一切意識しない。
"""

import sqlite3
from pathlib import Path
from typing import Iterable, List

from Model.db_path import DEFAULT_DB_PATH
from Model.task.task import Task

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    assignee TEXT NOT NULL,
    due_date TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL
)
"""

# UPDATE文のカラム名をf-stringで組み立てる箇所があるため、SQLインジェクションの
# 余地を無くすホワイトリスト。呼び出し元のTaskModel.update_task_fieldでも
# 別途EDITABLE_FIELDSで検証しているが、このモジュール単体でも安全なように
# 二重にチェックする。
_EDITABLE_COLUMNS = {"name", "assignee", "due_date", "priority", "status"}


def connect(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """DBファイルへ接続する。ファイル・テーブルが無ければ作成する。

    db_path=":memory:" を渡すと、ディスクに書き出さないインメモリDBになる
    （テスト用。呼び出すたびに独立した空のDBが得られるので、テストどうしで
    状態が混ざらない）。
    """
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(_CREATE_TABLE_SQL)
    conn.commit()
    return conn


def fetch_all(conn: sqlite3.Connection) -> List[Task]:
    """登録済みタスクを全件取得する（id昇順 = 追加順）"""
    rows = conn.execute(
        "SELECT id, name, assignee, due_date, priority, status FROM tasks ORDER BY id"
    ).fetchall()
    return [
        Task(id=r[0], name=r[1], assignee=r[2], due_date=r[3], priority=r[4], status=r[5])
        for r in rows
    ]


def insert(conn: sqlite3.Connection, task: Task) -> Task:
    """タスクを1件追加する。idはSQLite側の自動採番で上書きする
    （呼び出し側が渡したtask.id=0は無視する。CSVインポートなど、id未採番の
    Taskインスタンスをそのまま渡せるようにするため）。同じTaskインスタンスを
    id設定済みで返す。
    """
    cursor = conn.execute(
        "INSERT INTO tasks (name, assignee, due_date, priority, status) VALUES (?, ?, ?, ?, ?)",
        (task.name, task.assignee, task.due_date, task.priority, task.status),
    )
    conn.commit()
    task.id = cursor.lastrowid
    return task


def update_field(conn: sqlite3.Connection, task_id: int, field: str, value: str) -> None:
    """タスク1件の1項目を書き換える"""
    if field not in _EDITABLE_COLUMNS:
        raise ValueError(f"更新できない項目です: {field}")
    conn.execute(f"UPDATE tasks SET {field} = ? WHERE id = ?", (value, task_id))
    conn.commit()


def delete(conn: sqlite3.Connection, task_ids: Iterable[int]) -> None:
    """複数のタスクをまとめて削除する"""
    ids = list(task_ids)
    if not ids:
        return
    placeholders = ",".join("?" for _ in ids)
    conn.execute(f"DELETE FROM tasks WHERE id IN ({placeholders})", ids)
    conn.commit()
