"""
Model
-----
タスクのCSV書き出し・読み込み。tkinterに依存しない純粋なI/Oロジック。
「設定」タブの書き出し/読み込みボタンから、Presenter経由で呼ばれる。
"""

import csv
from typing import List, Tuple

from Model.task import Task

FIELDNAMES = ["name", "assignee", "due_date", "priority", "status", "tags", "memo"]


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
                    "tags": ",".join(t.tags),
                    "memo": t.memo,
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
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                skipped += 1
                continue
            tags_raw = row.get("tags") or ""
            tasks.append(
                Task(
                    name=name,
                    assignee=row.get("assignee", ""),
                    due_date=row.get("due_date", ""),
                    priority=row.get("priority") or "中",
                    status=row.get("status") or "未着手",
                    tags=[t.strip() for t in tags_raw.split(",") if t.strip()],
                    memo=row.get("memo", ""),
                )
            )
    return tasks, skipped
