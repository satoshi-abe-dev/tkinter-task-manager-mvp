"""
view.task — タスク一覧タブの View 層。フォルダ ＝ この名前空間。

再エクスポートするのは抽象クラス TaskListView（contract.py）だけ。Tkinter 実装
(TkTaskListFrame) をここで import すると、抽象 View 目的で
`task_manager_tkinter.view.task` を読むだけで tkinter を巻き込んでしまう
（test_presenter.py が tkinter 無しで動く前提を壊す）ため、Tk 実装は
完全モジュールパス
`task_manager_tkinter.view.task.tk_frame` から import すること。
"""

from task_manager_tkinter.view.task.contract import TaskListView

__all__ = ["TaskListView"]
