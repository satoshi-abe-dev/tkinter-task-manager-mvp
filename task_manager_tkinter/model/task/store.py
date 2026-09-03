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

from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, List, Optional

from task_manager_tkinter.model.lib import task_db
from task_manager_tkinter.model.lib.db_path import DEFAULT_DB_PATH
from task_manager_tkinter.model.task.entity import Task

# 一覧タブのインライン編集で書き換えを許すフィールド
EDITABLE_FIELDS = {"name", "assignee", "due_date", "priority", "status"}


def _seed_tasks() -> List[Task]:
    """デモ用の初期データ。

    期限日は「初回起動した日」を基準に相対的に決める。既定の通知設定
    （notify_enabled=True / notify_days_before=3）のもとで、一覧タブの期限ハイライトが
    初回から「白2・黄2・赤1」に見えるように配置している（黄＝期限が近い、赤＝超過）。

    呼び出すたびに新しいTaskインスタンスを作る（add_taskはtask.idをその場で
    書き換えるため、複数のTaskModelインスタンス間で同じTaskオブジェクトを
    使い回すとidが競合する）。
    """
    today = date.today()

    def due(offset_days: int) -> str:
        return (today + timedelta(days=offset_days)).strftime("%Y-%m-%d")

    return [
        # 黄: 期限が近い（today+1 / today+2 とも警告しきい値 today+3 以内）
        Task("Prepare Quotation", "Sato", due(1), "High", "In Progress"),
        Task("Prepare Meeting Materials", "Tanaka", due(2), "Medium", "Not Started"),
        # 赤: 期限超過（Statusも Overdue）
        Task("Write Release Notes", "Suzuki", due(-2), "High", "Overdue"),
        # 白: Done は常にハイライト対象外
        Task("Expense Report", "Sato", due(30), "Low", "Done"),
        # 白: 警告しきい値より先（today+7 > today+3）
        Task("Design Review", "Tanaka", due(7), "Medium", "In Progress"),
    ]


class TaskModel:
    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        # デモデータを入れるのは「DBファイルがまだ存在しない＝正真正銘の初回起動」の
        # ときだけ。connect() がファイルを作ってしまうので、その前に判定しておく。
        # （":memory:" は毎回まっさらな使い捨てDBなので常に初回扱い＝テスト用）
        first_run = db_path == ":memory:" or not Path(db_path).exists()

        self._conn = task_db.connect(db_path)
        self._tasks: List[Task] = task_db.fetch_all(self._conn)
        self._dirty = False
        if self._tasks:
            self._next_id = max(t.id for t in self._tasks) + 1
        else:
            self._next_id = 1
            if first_run:
                # 初回起動: デモ用の初期データを投入してすぐ保存する。
                # 2回目以降にユーザーが全タスクを削除しても、app.db は残るので
                # 「空のまま」になり、デモデータは復活しない。
                for task in _seed_tasks():
                    self.add_task(task)
                self.save()

    def close(self) -> None:
        """DB接続を閉じる。アプリはプロセス終了まで開きっぱなしで問題ないが、
        テストで一時ファイルを消す前などに明示的に閉じる（特にWindowsは
        開いているファイルを削除できないため）。"""
        self._conn.close()

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
