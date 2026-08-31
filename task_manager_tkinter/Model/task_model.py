"""
Model
-----
タスクの保持・追加・更新のみを行う。View や Presenter のことは一切知らない。
"""

from typing import Iterable, List

from Model.task import Task

# 一覧タブのインライン編集で書き換えを許すフィールド
EDITABLE_FIELDS = {"name", "assignee", "due_date", "priority", "status"}


class TaskModel:
    def __init__(self) -> None:
        self._next_id = 1
        self._tasks: List[Task] = []
        # デモ用の初期データ
        for task in (
            Task("見積書作成", "佐藤", "2026-09-02", "高", "進行中"),
            Task("定例MTG資料準備", "田中", "2026-09-01", "中", "未着手"),
            Task("リリースノート執筆", "鈴木", "2026-08-29", "高", "遅延"),
            Task("経費精算", "佐藤", "2026-09-05", "低", "完了"),
            Task("デザインレビュー", "田中", "2026-09-03", "中", "進行中"),
        ):
            self._register(task)

    def _register(self, task: Task) -> Task:
        task.id = self._next_id
        self._next_id += 1
        self._tasks.append(task)
        return task

    def list_tasks(self) -> List[Task]:
        """登録済みタスクの一覧を返す"""
        return list(self._tasks)

    def add_task(self, task: Task) -> Task:
        """タスクを1件追加する。idを採番して返す"""
        return self._register(task)

    def add_blank_task(self) -> Task:
        """全項目が空のタスクを1件追加する（一覧タブの「追加」ボタン用）。

        タスク名だけは空のままにせず、採番したidを使って「タスクN」という
        仮の名前を入れる。件数を数えて連番にすると、削除後に追加した時に
        番号が重複しうるため、idベースで一意性を保つ。
        """
        task = self._register(Task(name="", assignee="", due_date="", priority="", status=""))
        task.name = f"タスク{task.id}"
        return task

    def delete_tasks(self, task_ids: Iterable[int]) -> None:
        """指定した複数のタスクを削除する（一覧タブの「削除」ボタン用。複数選択に対応）"""
        ids = set(task_ids)
        self._tasks = [t for t in self._tasks if t.id not in ids]

    def update_task_field(self, task_id: int, field: str, value: str) -> None:
        """指定したタスクの1項目を書き換える（一覧タブのインライン編集用）"""
        if field not in EDITABLE_FIELDS:
            raise ValueError(f"編集できない項目です: {field}")
        for task in self._tasks:
            if task.id == task_id:
                setattr(task, field, value)
                return
        raise ValueError(f"該当するタスクが見つかりません: id={task_id}")
