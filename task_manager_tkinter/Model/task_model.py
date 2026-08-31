"""
Model
-----
タスクの保持・追加のみを行う。View や Presenter のことは一切知らない。
"""

from typing import List

from Model.task import Task


class TaskModel:
    def __init__(self) -> None:
        # デモ用の初期データ
        self._tasks: List[Task] = [
            Task("見積書作成", "佐藤", "2026-09-02", "高", "進行中"),
            Task("定例MTG資料準備", "田中", "2026-09-01", "中", "未着手"),
            Task("リリースノート執筆", "鈴木", "2026-08-29", "高", "遅延"),
            Task("経費精算", "佐藤", "2026-09-05", "低", "完了"),
            Task("デザインレビュー", "田中", "2026-09-03", "中", "進行中"),
        ]

    def list_tasks(self) -> List[Task]:
        """登録済みタスクの一覧を返す"""
        return list(self._tasks)

    def add_task(self, task: Task) -> None:
        """タスクを1件追加する"""
        self._tasks.append(task)
