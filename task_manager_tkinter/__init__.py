"""
task_manager_tkinter — MVP パターンのサンプル（タスク管理アプリ）

ルートパッケージ。フォルダ階層がそのままクラスの名前空間になる:
    task_manager_tkinter/model/task/     -> task_manager_tkinter.model.task.TaskModel
    task_manager_tkinter/view/settings/  -> task_manager_tkinter.view.settings.SettingsView

各サブパッケージの __init__.py が公開クラスを再エクスポートしているため、
利用側は「所在フォルダのドット表記」でそのままクラスを import できる。
"""
