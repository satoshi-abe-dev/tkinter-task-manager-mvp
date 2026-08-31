"""
View（抽象層）— タスク一覧タブ
------------------------------
Presenterが依存する「契約」だけを定義する。
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional

from Model.task.task import Task


class TaskListView(ABC):
    @abstractmethod
    def show_tasks(self, tasks: List[Task]) -> None:
        """タスク一覧を表示する"""

    @abstractmethod
    def set_on_cell_edited(
        self, handler: Callable[[int, str, str], None]
    ) -> None:
        """セルのインライン編集が確定した時に呼ばれるハンドラを登録する。
        引数: (task_id, field, new_value)
        """

    @abstractmethod
    def set_on_column_clicked(self, handler: Callable[[str], None]) -> None:
        """カラムのヘッダーがクリックされた時に呼ばれるハンドラを登録する。
        引数: field（クリックされた列名）
        """

    @abstractmethod
    def show_sort_state(self, field: Optional[str], ascending: bool) -> None:
        """現在のソート対象列・昇順/降順を見た目に反映する（列見出しの矢印など）。
        field が None の場合はソートされていない状態を表す。
        """

    @abstractmethod
    def set_on_add_click(self, handler: Callable[[], None]) -> None:
        """「追加」ボタン押下時に呼ばれるハンドラを登録する"""

    @abstractmethod
    def set_on_delete_click(self, handler: Callable[[List[int]], None]) -> None:
        """「削除」ボタン押下時に呼ばれるハンドラを登録する。
        引数: task_ids（削除対象。複数選択している場合は選択中の全件）。
        確認ポップアップの表示・選択行の特定はView側で行い、「はい」が選ばれた
        場合のみこのハンドラを呼ぶ。
        """

    @abstractmethod
    def select_task(self, task_id: int) -> None:
        """指定したタスクを選択状態にする（追加直後に一覧を最新化した後などに使う）"""

    @abstractmethod
    def show_due_date_highlights(self, highlights: Dict[int, str]) -> None:
        """期限が近い/過ぎているタスクの行を見た目で強調する。
        引数: task_id → "warning"（期限が近い）または "overdue"（期限超過）の対応表。
        表に含まれないtask_idは通常表示に戻す。
        """

    @abstractmethod
    def set_on_export_click(self, handler: Callable[[], None]) -> None:
        """「書き出し」ボタン押下時に呼ばれるハンドラを登録する"""

    @abstractmethod
    def set_on_import_click(self, handler: Callable[[], None]) -> None:
        """「読み込み」ボタン押下時に呼ばれるハンドラを登録する"""

    @abstractmethod
    def ask_save_path(self) -> Optional[str]:
        """書き出し先のファイルパスをユーザーに選ばせる。キャンセル時はNone"""

    @abstractmethod
    def ask_open_path(self) -> Optional[str]:
        """読み込み元のファイルパスをユーザーに選ばせる。キャンセル時はNone"""

    @abstractmethod
    def show_message(self, title: str, message: str) -> None:
        """メッセージをポップアップ表示する"""

    @abstractmethod
    def set_dirty(self, dirty: bool) -> None:
        """save()していない変更があるかどうかの表示を切り替える。
        Saveボタン自体はこのタブの外(TkMainWindow側)にあるため、ここでは
        あくまで表示のみを行う。
        """
