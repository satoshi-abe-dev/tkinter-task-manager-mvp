"""
View（抽象層）— 新規登録タブ
----------------------------
Presenterが依存する「契約」だけを定義する。
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional


class NewTaskView(ABC):
    @abstractmethod
    def set_on_register_click(self, handler: Callable[[], None]) -> None:
        """「登録」ボタン押下時に呼ばれるハンドラを登録する"""

    @abstractmethod
    def set_on_cancel_click(self, handler: Callable[[], None]) -> None:
        """「キャンセル」ボタン押下時に呼ばれるハンドラを登録する"""

    @abstractmethod
    def get_form_values(self) -> dict:
        """フォームの入力値を dict で返す
        キー: name, assignee, due_date, priority, status, tags, memo
        """

    @abstractmethod
    def show_name_error(self, message: Optional[str]) -> None:
        """タスク名欄のエラーメッセージを表示する。Noneでエラー表示を消す"""

    @abstractmethod
    def clear_form(self) -> None:
        """フォームを初期状態に戻す"""
