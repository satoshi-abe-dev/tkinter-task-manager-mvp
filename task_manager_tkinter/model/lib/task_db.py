"""
Model — タスクの永続化(SQLite)
--------------------------------
タスクをSQLiteに保存・読み込みする、tkinterに依存しない純粋なI/Oロジック。
csv_io.pyと同じ位置づけで、TaskModel(model/task/store.py)がこのモジュールを介して
DBを読み書きする。

書き込みは「編集のたびに1件ずつ」ではなく、TaskModel.save()が呼ばれた時に
その時点のメモリ上の状態をまるごとDBへ反映するスナップショット方式にしている。
これは、ユーザーが明示的に「Save」ボタンを押すまではディスクに何も書き込まれ
ないようにするため（保存前の操作を間違えても、保存しなければ次回起動時には
直前の保存状態に戻せる）。
"""

import sqlite3
from pathlib import Path
from typing import List

from task_manager_tkinter.model.lib.db_path import DEFAULT_DB_PATH
from task_manager_tkinter.model.task.entity import Task

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    assignee TEXT NOT NULL,
    due_date TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL
)
"""


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
    """保存済みタスクを全件取得する（id昇順 = 追加順）"""
    rows = conn.execute(
        "SELECT id, name, assignee, due_date, priority, status FROM tasks ORDER BY id"
    ).fetchall()
    return [
        Task(id=r[0], name=r[1], assignee=r[2], due_date=r[3], priority=r[4], status=r[5])
        for r in rows
    ]


def replace_all(conn: sqlite3.Connection, tasks: List[Task]) -> None:
    """DBの内容を、渡されたタスク一覧でまるごと置き換える(「Save」操作用)。

    差分計算はせず、既存の行を全部消してから入れ直すシンプルな方式
    （タスク管理アプリの規模ではこれで十分速い）。idも明示的に書き込む
    ことで、TaskModel側で採番した既存タスクのidをそのまま維持する。
    """
    conn.execute("DELETE FROM tasks")
    conn.executemany(
        "INSERT INTO tasks (id, name, assignee, due_date, priority, status) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [(t.id, t.name, t.assignee, t.due_date, t.priority, t.status) for t in tasks],
    )
    conn.commit()
