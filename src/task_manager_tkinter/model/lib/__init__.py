"""
model.lib — Home for pure I/O modules that hold no classes
------------------------------------------------------------
db_path / db_backup / task_db / settings_db / csv_io. None of them depend on
tkinter; they only expose functions (the equivalent of a Tcl "proc"
namespace). To avoid circular imports, this package's __init__.py
re-exports nothing.
"""
