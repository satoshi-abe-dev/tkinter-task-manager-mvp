"""
エントリーポイント
------------------
Model / View / Presenter の各フォルダから読み込んで組み立てて起動する。

フォルダ構成:
    task_manager_tkinter/
        main.py          <- これ（Model, View, Presenterと同じ階層）
        Model/
            task/
                task.py               Task（データクラス）
                task_model.py         TaskModel
                csv_io.py             CSV書き出し/読み込み（純粋なI/O）
            settings/
                settings_model.py     Settings / SettingsModel
        View/
            task/
                task_list_view.py     TaskListView（抽象クラス）
                tk_task_list_frame.py Tkinter実装（タスク一覧タブ）
            settings/
                settings_view.py      SettingsView（抽象クラス）
                tk_settings_frame.py  Tkinter実装（設定タブ）
            tk_main_window.py         Tkinter実装（2タブをまとめるTkMainWindow）
        Presenter/
            task/
                task_list_presenter.py
            settings/
                settings_presenter.py

実行方法:
    このフォルダ(task_manager_tkinter)の直下で
        python3 main.py
※ GUIなので、Tcl/Tkが使えるお手元のPCで実行してください。
"""

from Model.settings.settings_model import SettingsModel
from Model.task.task_model import TaskModel
from Presenter.settings.settings_presenter import SettingsPresenter
from Presenter.task.task_list_presenter import TaskListPresenter
from View.tk_main_window import TkMainWindow


def main() -> None:
    task_model = TaskModel()
    settings_model = SettingsModel()

    window = TkMainWindow()

    task_list_presenter = TaskListPresenter(task_model, settings_model, window.task_list_frame)
    SettingsPresenter(
        settings_model,
        window.settings_frame,
        on_settings_saved=task_list_presenter.refresh,
    )

    window.run()


if __name__ == "__main__":
    main()
