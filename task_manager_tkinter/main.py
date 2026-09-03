"""
エントリーポイント
------------------
model / view / presenter の各フォルダから読み込んで組み立てて起動する。
フォルダ階層がそのままクラスの名前空間になっている
（例: model/task/ ⇔ task_manager_tkinter.model.task.TaskModel）。

フォルダ構成（ファイル名は役割を表し、フォルダ名は繰り返さない）:
    task_manager_tkinter/          ルートパッケージ
        main.py          <- これ（model, view, presenterと同じ階層）
        data/            アプリのSQLiteデータベース(app.db)の置き場。実行時に自動作成される
            backups/           設定した間隔(既定15分)ごとの自動バックアップ(直近24時間分)の置き場
        model/
            lib/            クラスを持たない純粋I/Oモジュールの置き場
                db_path.py        DBファイルの既定パス（task/settingsで共有）
                db_backup.py      app.dbのバックアップ・世代管理（純粋なI/O）
                task_db.py        タスクの永続化(SQLite、純粋なI/O)
                settings_db.py    設定の永続化(SQLite、純粋なI/O)
                csv_io.py         CSV書き出し/読み込み（純粋なI/O）
            task/
                entity.py         Task（データクラス）＋ PRIORITIES / STATUSES
                store.py          TaskModel（メモリ上のタスク集合を保持し永続化を委譲）
            settings/
                entity.py         Settings（データクラス）
                store.py          SettingsModel
        view/
            callbacks.py          CallbackRegistryMixin（両tk_frame共通のコールバック登録mixin）
            task/
                contract.py       TaskListView（抽象クラス＝Presenterが依存する契約）
                tk_frame.py       Tkinter実装（タスク一覧タブ）
            settings/
                contract.py       SettingsView（抽象クラス＝Presenterが依存する契約）
                tk_frame.py       Tkinter実装（設定タブ）
            tk_main_window.py     Tkinter実装（2タブをまとめるTkMainWindow）
        presenter/            （タブごとにファイル1個。サブフォルダは作らない）
            task.py               TaskListPresenter
            settings.py           SettingsPresenter

実行方法（どちらでも可）:
    - リポジトリのルート（task_manager_tkinter/ の親フォルダ）で
        python3 -m task_manager_tkinter.main
    - ファイル指定で直接
        python3 task_manager_tkinter/main.py
      または  cd task_manager_tkinter && python3 main.py
      （下の sys.path ブートストラップが絶対 import を通す）
※ GUIなので、Tcl/Tkが使えるお手元のPCで実行してください。
※ タスク・設定はSQLite(標準ライブラリのsqlite3、追加インストール不要)で
  永続化される。DBファイルは初回実行時にdata/app.dbとして作成される。
  編集は常に即座にDBへ保存される(Auto Save)。Saveボタンや「未保存」表示は無い。
※ 設定タブの「Backup」欄で指定した間隔（既定15分）ごとに、app.dbへの変更を検知して
  自動的にバックアップを取る（前回のバックアップ以降に変更が無ければスキップする）。
  直近24時間分だけ残し、古いものは自動的に削除する。ディスク破損など、DBファイル
  自体が壊れてしまった場合の保険。
  間隔を実行中に変更した場合、次にタイマーが発火したタイミングから新しい間隔が
  反映される（既にスケジュール済みの分を即座にキャンセルして再スケジュールはしない）。
"""

import os
import sys

# `python main.py` / `python task_manager_tkinter/main.py` のようにファイル指定で
# 直接起動されると、この時点では task_manager_tkinter パッケージが import パスに
# 無い（__package__ が未設定）。リポジトリのルート（このファイルの2つ上）を
# sys.path に足して、`python -m task_manager_tkinter.main` と同じ絶対 import が
# 通るようにする。-m で起動された場合は __package__ が設定済みなので何もしない。
if __package__ in (None, ""):
    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

from task_manager_tkinter.model.lib.db_backup import backup_and_rotate  # noqa: E402
from task_manager_tkinter.model.lib.db_path import DEFAULT_DB_PATH  # noqa: E402
from task_manager_tkinter.model.settings import SettingsModel  # noqa: E402
from task_manager_tkinter.model.task import TaskModel  # noqa: E402
from task_manager_tkinter.presenter.settings import SettingsPresenter  # noqa: E402
from task_manager_tkinter.presenter.task import TaskListPresenter  # noqa: E402
from task_manager_tkinter.view.tk_main_window import TkMainWindow  # noqa: E402

_MIN_BACKUP_INTERVAL_MINUTES = 1  # 0以下が設定されても暴走しないようにする下限


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

    # 設定タブで指定された間隔(既定15分)ごとに、app.dbが前回のバックアップ以降に
    # 変更されていないか確認し、変更があればバックアップを取る。ファイルの更新日時
    # (mtime)を比較するだけなので、どの編集操作が書き込んだかは区別しない。
    last_backup_mtime = None

    def check_and_backup() -> None:
        nonlocal last_backup_mtime
        if os.path.exists(DEFAULT_DB_PATH):
            current_mtime = os.path.getmtime(DEFAULT_DB_PATH)
            if current_mtime != last_backup_mtime:
                backup_and_rotate(DEFAULT_DB_PATH)
                last_backup_mtime = current_mtime
        interval_minutes = max(
            _MIN_BACKUP_INTERVAL_MINUTES, settings_model.get().backup_interval_minutes
        )
        window.schedule(interval_minutes * 60 * 1000, check_and_backup)

    initial_interval_minutes = max(
        _MIN_BACKUP_INTERVAL_MINUTES, settings_model.get().backup_interval_minutes
    )
    window.schedule(initial_interval_minutes * 60 * 1000, check_and_backup)

    window.run()


if __name__ == "__main__":
    main()
