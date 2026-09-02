"""
model.lib — クラスを持たない純粋 I/O モジュールの置き場
--------------------------------------------------------
db_path / db_backup / task_db / settings_db / csv_io。いずれも tkinter に依存せず、
関数だけを公開する（Tcl でいう proc の名前空間に相当）。循環 import を避けるため、
このパッケージの __init__.py では何も再エクスポートしない。
"""
