"""
エントリーポイント
------------------
Model / View / Presenter の各フォルダから読み込んで組み立てて起動する。

フォルダ構成:
    task_manager_tkinter/
        main.py          <- これ（Model, View, Presenterと同じ階層）
        Model/
            task.py               Task（データクラス）
            task_model.py         TaskModel
            settings_model.py     Settings / SettingsModel
            csv_io.py             CSV書き出し/読み込み（純粋なI/O）
        View/
            task_list_view.py     TaskListView（抽象クラス）
            new_task_view.py      NewTaskView（抽象クラス）
            settings_view.py      SettingsView（抽象クラス）
            tk_main_window.py     Tkinter実装（3タブぶんのFrame + TkMainWindow）
        Presenter/
            task_list_presenter.py
            new_task_presenter.py
            settings_presenter.py

実行方法:
    このフォルダ(task_manager_tkinter)の直下で
        python3 main.py
※ GUIなので、Tcl/Tkが使えるお手元のPCで実行してください。
"""

from Model.settings_model import SettingsModel
from Model.task_model import TaskModel
from Presenter.new_task_presenter import NewTaskPresenter
from Presenter.settings_presenter import SettingsPresenter
from Presenter.task_list_presenter import TaskListPresenter
from View.tk_main_window import TkMainWindow


def main() -> None:
    task_model = TaskModel()
    settings_model = SettingsModel()

    window = TkMainWindow()

    task_list_presenter = TaskListPresenter(task_model, window.task_list_frame)
    NewTaskPresenter(
        task_model,
        window.new_task_frame,
        on_task_added=task_list_presenter.refresh,
    )
    SettingsPresenter(
        settings_model,
        task_model,
        window.settings_frame,
        on_tasks_imported=task_list_presenter.refresh,
    )

    window.run()


if __name__ == "__main__":
    main()
