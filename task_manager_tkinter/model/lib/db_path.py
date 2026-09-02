"""
アプリ全体で使うSQLiteデータベースファイルの既定パス。
TaskModel・SettingsModelはそれぞれ独立した接続でこの同じファイルを開き、
tasksテーブル・settingsテーブルにそれぞれ読み書きする（お互いの存在は知らない）。

テスト(test_presenter.py)では、この既定パスの代わりに":memory:"を渡すことで、
ディスクに何も残さない使い捨てのDBを使う（テストどうしで状態が混ざらない）。
"""

from pathlib import Path

# task_manager_tkinter/data/app.db
# カレントディレクトリに依存しないよう、このファイル自身の場所を基準にする。
# このファイルは task_manager_tkinter/model/lib/ にあるので、parent を 3 つ
# 遡るとパッケージルート(task_manager_tkinter/)になる。
DEFAULT_DB_PATH = str(
    Path(__file__).resolve().parent.parent.parent / "data" / "app.db"
)
