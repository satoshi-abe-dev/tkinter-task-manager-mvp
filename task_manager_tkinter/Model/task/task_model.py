"""
Model
-----
タスクの保持・追加・更新・削除のドメインロジックだけを持つ。View や Presenter
のことは一切知らない。

編集操作(追加/更新/削除)はメモリ上の_tasksだけを書き換え、その場ではDBへ
書き込まない。実際にSQLiteへ反映されるのは save() が明示的に呼ばれた時
（一覧タブの「Save」ボタン押下時）だけ。これにより、保存前に操作を間違えても、
保存さえしなければ次回起動時には直前の保存状態にそのまま戻る（アプリの
再起動が「全部取り消し」の代わりになる）。
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
        self._dirty = False
        if self._tasks:
            self._next_id = max(t.id for t in self._tasks) + 1
        else:
            # DBにタスクが1件も無い場合は、デモ用の初期データを投入してすぐ保存する
            # （初回起動を想定。ユーザーが後から全タスクを削除して保存した場合も、
            # 次回起動時にまたこのデモデータが入る点に注意。「空」と「未初期化」を
            # 区別していない、ポートフォリオ用の割り切り）。
            self._next_id = 1
            for task in _seed_tasks():
                self.add_task(task)
            self.save()

    def list_tasks(self) -> List[Task]:
        """登録済みタスクの一覧を返す"""
        return list(self._tasks)

    def get_task(self, task_id: int) -> Optional[Task]:
        """idで1件だけ取得する。見つからなければNone"""
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def is_dirty(self) -> bool:
        """save()していない変更があるかどうか"""
        return self._dirty

    def save(self) -> None:
        """現在のメモリ上の状態をまるごとDBへ反映する（一覧タブの「Save」ボタン用）"""
        task_db.replace_all(self._conn, self._tasks)
        self._dirty = False

    def add_task(self, task: Task) -> Task:
        """タスクを1件追加する。idを採番して返す（DBへの反映はsave()を待つ）"""
        task.id = self._next_id
        self._next_id += 1
        self._tasks.append(task)
        self._dirty = True
        return task

    def add_blank_task(self) -> Task:
        """全項目が空のタスクを1件追加する（一覧タブの「追加」ボタン用）。

        タスク名だけは空のままにせず、採番したidを使って「Task N」という
        仮の名前を入れる。件数を数えて連番にすると、削除後に追加した時に
        番号が重複しうるため、idベースで一意性を保つ。
        """
        task = self.add_task(Task(name="", assignee="", due_date="", priority="", status=""))
        task.name = f"Task {task.id}"
        return task

    def delete_tasks(self, task_ids: Iterable[int]) -> None:
        """指定した複数のタスクを削除する（一覧タブの「削除」ボタン用。複数選択に対応）"""
        ids = set(task_ids)
        self._tasks = [t for t in self._tasks if t.id not in ids]
        self._dirty = True

    def update_task_field(self, task_id: int, field: str, value: str) -> None:
        """指定したタスクの1項目を書き換える（一覧タブのインライン編集用）"""
        if field not in EDITABLE_FIELDS:
            raise ValueError(f"編集できない項目です: {field}")
        for task in self._tasks:
            if task.id == task_id:
                setattr(task, field, value)
                self._dirty = True
                return
        raise ValueError(f"該当するタスクが見つかりません: id={task_id}")
