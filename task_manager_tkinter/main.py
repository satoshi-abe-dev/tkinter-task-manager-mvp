"""
エントリーポイント
------------------
Model / View / Presenter の各フォルダから読み込んで組み立てて起動する。

フォルダ構成:
    task_manager_tkinter/
        main.py          <- これ（Model, View, Presenterと同じ階層）
        data/            アプリのSQLiteデータベース(app.db)の置き場。実行時に自動作成される
        Model/
            db_path.py            DBファイルの既定パス（task/settingsで共有）
            task/
                task.py               Task（データクラス）
                task_model.py         TaskModel
                task_db.py            タスクの永続化(SQLite、純粋なI/O)
                csv_io.py             CSV書き出し/読み込み（純粋なI/O）
            settings/
                settings_model.py     Settings / SettingsModel
                settings_db.py        設定の永続化(SQLite、純粋なI/O)
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
※ タスク・設定はSQLite(標準ライブラリのsqlite3、追加インストール不要)で
  自動的に永続化される。DBファイルは初回実行時にdata/app.dbとして作成される。
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
