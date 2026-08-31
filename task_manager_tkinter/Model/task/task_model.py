"""
Model
-----
タスクの保持・追加・更新・削除のドメインロジックだけを持つ。View や Presenter
のことは一切知らない。永続化はModel.task.task_db（SQLite）に委譲しており、
TaskModel自身はSQLの詳細を知らない。
"""

from typing import Iterable, List, Optional

from Model.db_path import DEFAULT_DB_PATH
from Model.task import task_db
from Model.task.task import Task

# 一覧タブのインライン編集で書き換えを許すフィールド
EDITABLE_FIELDS = {"name", "assignee", "due_date", "priority", "status"}


def _seed_tasks() -> List[Task]:
    """デモ用の初期データ。呼び出すたびに新しいTaskインスタンスを作る
    （add_taskはtask.idをその場で書き換えるため、複数のTaskModelインスタンス間で
    同じTaskオブジェクトを使い回すとidが競合する）。
    """
    return [
        Task("Prepare Quotation", "Sato", "2026-09-02", "High", "In Progress"),
        Task("Prepare Meeting Materials", "Tanaka", "2026-09-01", "Medium", "Not Started"),
        Task("Write Release Notes", "Suzuki", "2026-08-29", "High", "Overdue"),
        Task("Expense Report", "Sato", "2026-09-05", "Low", "Done"),
        Task("Design Review", "Tanaka", "2026-09-03", "Medium", "In Progress"),
    ]


class TaskModel:
    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self._conn = task_db.connect(db_path)
        self._tasks: List[Task] = task_db.fetch_all(self._conn)
        if not self._tasks:
            # DBにタスクが1件も無い場合は、デモ用の初期データを投入する
            # （初回起動を想定）。ユーザーが後から全タスクを削除した場合も、
            # 次回起動時にまたこのデモデータが入る点に注意（「空」と
            # 「未初期化」を区別していない。ポートフォリオ用の割り切り）。
            for task in _seed_tasks():
                self.add_task(task)

    def list_tasks(self) -> List[Task]:
        """登録済みタスクの一覧を返す"""
        return list(self._tasks)

    def get_task(self, task_id: int) -> Optional[Task]:
        """idで1件だけ取得する。見つからなければNone"""
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def add_task(self, task: Task) -> Task:
        """タスクを1件追加する。idを採番して返す（DBへも書き込む）"""
        task_db.insert(self._conn, task)
        self._tasks.append(task)
        return task

    def add_blank_task(self) -> Task:
        """全項目が空のタスクを1件追加する（一覧タブの「追加」ボタン用）。

        タスク名だけは空のままにせず、採番したidを使って「Task N」という
        仮の名前を入れる。件数を数えて連番にすると、削除後に追加した時に
        番号が重複しうるため、idベースで一意性を保つ。
        """
        task = self.add_task(Task(name="", assignee="", due_date="", priority="", status=""))
        task.name = f"Task {task.id}"
        task_db.update_field(self._conn, task.id, "name", task.name)
        return task

    def delete_tasks(self, task_ids: Iterable[int]) -> None:
        """指定した複数のタスクを削除する（一覧タブの「削除」ボタン用。複数選択に対応）"""
        ids = set(task_ids)
        task_db.delete(self._conn, ids)
        self._tasks = [t for t in self._tasks if t.id not in ids]

    def update_task_field(self, task_id: int, field: str, value: str) -> None:
        """指定したタスクの1項目を書き換える（一覧タブのインライン編集用）"""
        if field not in EDITABLE_FIELDS:
            raise ValueError(f"編集できない項目です: {field}")
        for task in self._tasks:
            if task.id == task_id:
                task_db.update_field(self._conn, task_id, field, value)
                setattr(task, field, value)
                return
        raise ValueError(f"該当するタスクが見つかりません: id={task_id}")
