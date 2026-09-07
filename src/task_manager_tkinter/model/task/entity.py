"""
Task（データクラス）
--------------------
タスク1件分のデータを表す。ロジックは持たない。
"""

from dataclasses import dataclass

# 優先度・ステータスの取りうる値と、意味のある並び順（低い方から高い方へ など）。
# フォームの選択肢や一覧のソート順など、複数箇所から共通で参照する。
# ステータスはワークフローの状態のみ。「期限切れ」は状態としては持たず、
# due_date が過去かどうかから毎回導出して赤くハイライトする（Presenter 側）。
PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Not Started", "In Progress", "Done"]


@dataclass
class Task:
    name: str
    assignee: str
    due_date: str
    priority: str  # "High" | "Medium" | "Low"
    status: str  # "Not Started" | "In Progress" | "Done"
    # TaskModelが追加時に自動採番する。呼び出し側は指定しなくてよい。
    # 一覧のインライン編集時に「どのタスクか」を安定して特定するために使う
    # （一覧の並び順やインデックスに依存させないため）。
    id: int = 0
