"""
Model
-----
タスクのCSV書き出し・読み込み。tkinterに依存しない純粋なI/Oロジック。
「タスク一覧」タブの書き出し/読み込みボタンから、Presenter経由で呼ばれる。

例外はここでは握りつぶさず、そのまま呼び出し側(Presenter)へ投げる。
起こりうるのは OSError(ファイルが開けない/権限/ディスク等)、
UnicodeDecodeError(文字コード不正。ValueErrorのサブクラス)、
csv.Error(壊れたCSV)、ValueError(必要な列が無い等。下記で明示的にraise)。
Presenter がこれらを捕捉して view.show_message() でユーザーに伝える。
"""

import csv
from typing import List, Tuple

from task_manager_tkinter.model.task.entity import STATUSES, Task

FIELDNAMES = ["name", "assignee", "due_date", "priority", "status"]


def export_tasks_to_csv(tasks: List[Task], path: str) -> None:
    """タスク一覧をCSVファイルに書き出す"""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for t in tasks:
            writer.writerow(
                {
                    "name": t.name,
                    "assignee": t.assignee,
                    "due_date": t.due_date,
                    "priority": t.priority,
                    "status": t.status,
                }
            )


def import_tasks_from_csv(path: str) -> Tuple[List[Task], int]:
    """CSVファイルからタスクを読み込む。

    戻り値: (読み込めたTaskのリスト, タスク名が空でスキップした行数)
    """
    tasks: List[Task] = []
    skipped = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if "name" not in (reader.fieldnames or []):
            # 見出しに name 列が無い＝このアプリのCSVではない。
            # 全行 skip して「0件取り込み」と見せるより、はっきりエラーにする。
            raise ValueError(
                "The CSV file has no 'name' column — "
                "import a CSV that was exported by this app."
            )
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                skipped += 1
                continue
            # 旧バージョンが書き出した "Overdue" など、今は無いステータス値は
            # "Not Started" に寄せる（"Overdue" は状態ではなく due_date から導出する）。
            status = row.get("status") or "Not Started"
            if status not in STATUSES:
                status = "Not Started"
            tasks.append(
                Task(
                    name=name,
                    assignee=row.get("assignee", ""),
                    due_date=row.get("due_date", ""),
                    priority=row.get("priority") or "Medium",
                    status=status,
                )
            )
    return tasks, skipped
