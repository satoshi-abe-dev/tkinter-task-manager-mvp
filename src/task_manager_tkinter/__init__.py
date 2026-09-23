"""
task_manager_tkinter — Sample app (task manager) demonstrating the MVP pattern

Root package (src layout). Folder hierarchy = class namespace:
    src/task_manager_tkinter/model/task/     -> task_manager_tkinter.model.task.TaskModel
    src/task_manager_tkinter/view/settings/  -> task_manager_tkinter.view.settings.SettingsView

Each subpackage's __init__.py re-exports its public classes, so callers
import by the folder's dotted path directly.
"""
