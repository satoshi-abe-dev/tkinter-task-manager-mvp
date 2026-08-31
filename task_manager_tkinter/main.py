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
  永続化される。DBファイルは初回実行時にdata/app.dbとして作成される。
  ただしどちらのタブの変更も、タブの外（Notebookの直前の行、右端）にある
  共通の「Save」ボタンを押すまでDBには書き込まれない（保存前に間違えても、
  保存しなければ次回起動時には直前の保存状態に戻る）。ウィンドウを閉じようと
  した時、どちらかのタブに未保存の変更があれば保存するかどうかを確認する
  ダイアログを出す。
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
    settings_presenter = SettingsPresenter(
        settings_model,
        window.settings_frame,
        on_settings_saved=task_list_presenter.refresh,
    )

    def save_all() -> None:
        """共通の「Save」ボタン用。どちらのタブが今表示されているかに関わらず、
        両タブの未保存の変更をまとめて保存する。
        """
        task_list_presenter.on_save_click()
        settings_presenter.on_save_click()

    def has_any_unsaved_changes() -> bool:
        return task_list_presenter.has_unsaved_changes() or settings_presenter.has_unsaved_changes()

    def handle_close_request() -> None:
        """ウィンドウを閉じようとした時に呼ばれる。どちらかのタブに未保存の
        変更があれば、保存する/破棄する/キャンセルの3択を確認してから閉じる。
        """
        if not has_any_unsaved_changes():
            window.close()
            return
        choice = window.ask_save_discard_cancel(
            "Unsaved Changes",
            "You have unsaved changes.\nSave before closing?",
        )
        if choice is True:  # 保存する
            save_all()
            window.close()
        elif choice is False:  # 破棄する
            window.close()
        # choice is None（キャンセル）の場合は何もせず、ウィンドウを開いたままにする

    window.set_on_save_click(save_all)
    window.set_on_close_requested(handle_close_request)

    window.run()


if __name__ == "__main__":
    main()
