# mvp-pattern-sample-2

[English](README_en.md) | 日本語

Python (Tkinter) による MVP（Model-View-Presenter）デザインパターンのサンプル実装。
[mvp-pattern-sample-1](https://github.com/yanyayanyan1988/mvp-pattern-sample-1) の続編で、
「タブ付きの実務寄りなタスク管理アプリ」を題材にしている。

## スクリーンショット

> ⚠️ 以下は「新規登録」タブがあった旧バージョンのスクリーンショットです。
> 現在は「タスク一覧」「設定」の2タブ構成に変わっています（後述）。撮り直し次第、差し替えます。

| タスク一覧 | 設定 |
|---|---|
| ![タスク一覧タブ](docs/screenshots/task-list.png) | ![設定タブ](docs/screenshots/settings.png) |

## 目的

タブごとに異なる画面（タスク一覧・設定）を持つ、実務でありそうなTkinterデスクトップアプリを題材に、
MVPパターン（Model / View / Presenter）で責務を分離して実装したサンプル。

## 機能

- **タスク一覧タブ**: 登録済みタスクを表（`ttk.Treeview`）で一覧表示する。
  - セルをダブルクリックするとその場で編集できる（タスク名・担当・期限・優先度・ステータス）。
    優先度・ステータスは選択式（プルダウン）にして、不正な値が入らないようにしている。
  - 期限は`tkcalendar`のカレンダーをポップアップ表示して選択する。「現在の期限」を常時表示し、
    「この日に戻る」ボタンで月を移動しても元の設定に迷わず戻れる。
  - カラムヘッダーをクリックするとその列でソートする。同じ列を再クリックすると昇順/降順が
    切り替わり、見出しに▲/▼で表示される。優先度・ステータスは五十音順ではなく、
    意味のある順序（低→中→高、未着手→...→遅延）でソートされる。
  - 表の下にある「＋ 追加」「－ 削除」ボタン（隣接して表の幅いっぱいに配置）でタスクの
    追加・削除を行う。専用の登録フォームは持たない。
    - 「＋ 追加」を押すと、全項目が空のタスクが1件追加され、選択状態になる。タスク名だけは
      空のままにせず「タスクN」という仮の名前が入る（Nはタスクごとに振られる一意のid）。
      あとは他の行と同様に、インライン編集でタスク名・担当・期限・優先度・ステータスを埋めていく。
    - 「－ 削除」は行が選択されている時だけ押せる（未選択時は無効化）。押すと
      「本当に削除しますか？」の確認ポップアップ（OS標準のアラート）が出て、「はい」を選ぶと
      選択中の行を削除する。
- **設定タブ**: 通知（ON/OFF・タイミング）・一覧の表示件数・テーマを設定する。
  - 値を変更すると「未保存の変更があります」と表示され、「変更を保存」を押すまで反映されない。
  - タスクをCSVファイルへの書き出し／CSVファイルからの読み込みができる。

タブ自体・ボタンの見た目はあえてOS標準に近いスタイル（`ttk.Notebook`/`ttk.Button`のデフォルト）のままにしている。

## フォルダ構成

```
task_manager_tkinter/
    main.py                   エントリーポイント（Model, View, Presenterと同じ階層）
    test_presenter.py         2つのPresenterの単体テスト（tkinter不要）
    Model/
        task.py                Task（データクラス）
        task_model.py          TaskModel
        settings_model.py      Settings（データクラス）/ SettingsModel
        csv_io.py               CSV書き出し/読み込み（tkinterに依存しない純粋なI/O）
    View/
        task_list_view.py      TaskListView（抽象クラス）
        settings_view.py       SettingsView（抽象クラス）
        tk_main_window.py      Tkinter実装（2タブぶんのFrame + ウィンドウ全体）
    Presenter/
        task_list_presenter.py
        settings_presenter.py
```

## 各層の責務

| 層 | クラス | 責務 | 依存先 |
|---|---|---|---|
| Model | `TaskModel` | タスクの保持・追加（空欄タスクの追加を含む）・更新・削除のみ。UIのことは一切知らない。 | なし |
| Model | `SettingsModel` | 設定値の保持・更新のみ（メモリ上のみ、永続化はしない）。 | なし |
| Model | `csv_io` | タスクのCSV書き出し/読み込み。純粋なI/O関数。 | なし |
| View（抽象） | `TaskListView` / `SettingsView` | 各タブの「契約」（表示・入力取得・ハンドラ登録）を定義。 | なし |
| View（実装） | `tk_main_window.py`（`TkTaskListFrame` / `TkSettingsFrame` / `TkMainWindow`） | 上記の抽象をTkinter（`ttk.Notebook` + 標準ウィジェット）で実装。 | 各View抽象, tkinter |
| Presenter | `TaskListPresenter` / `SettingsPresenter` | 各タブの「画面の振る舞い」のロジック。バリデーション・Model更新・一覧のソート状態管理・タスクの追加/削除を担う。 | 対応するModel, 対応するView（抽象のみ） |

各PresenterはそれぞれのView抽象にしか依存していないため、View側の実装を差し替えても（Tkinter／別のGUIライブラリ／テスト用のFakeViewなど）Presenterのコードは変更不要。

## データフロー（「＋ 追加」を押した時）

1. ユーザーが「タスク一覧」タブの「＋ 追加」ボタンを押す。
2. `TkTaskListFrame`に登録済みのハンドラ（`TaskListPresenter.on_add_click`）が呼ばれる。
3. Presenterが`TaskModel.add_blank_task()`を呼ぶ。Modelは全項目が空のタスクを追加し、
   採番したidを使って「タスクN」という仮の名前を自動で入れる。
4. `refresh()`で一覧を最新化し、`view.select_task(task.id)`で追加した行を選択状態にする。
5. ユーザーは選択された行のセルをダブルクリックして、担当・期限・優先度・ステータスなどを
   インライン編集で埋めていく（既存タスクの編集と同じ仕組み）。

## 実行方法

`tkcalendar`（期限のカレンダー選択に使用）が必要なため、リポジトリ直下に仮想環境を作ってから実行する。
GUIを使うため、Tcl/Tkが使える環境で実行すること。

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cd task_manager_tkinter
../.venv/bin/python main.py
```

## テスト方法

`TkMainWindow`（および内部のFrame）の代わりにFakeView（各View抽象クラスの偽実装）を差し込むことで、
Tkinterを一切起動せずに2つのPresenterのロジックを検証する。

`test_presenter.py`は各`View.*_view`（抽象クラス）のみに依存し、`View.tk_main_window`（Tkinter実装）は
読み込まないため、tkinterが入っていない環境でも実行可能。

```bash
cd task_manager_tkinter
python3 test_presenter.py
```

CIでも、PR作成時・`main`へのpush時に同じテストが自動実行される（`.github/workflows/test.yml`）。

## 前提環境

- Python 3.14（Homebrew版）
- tkinter利用には `brew install python-tk@3.14` が別途必要（macOS標準の`/usr/bin`側は非推奨のTcl/Tk 8.5.9のため使用しない）
- GUIの実行には`tkcalendar`が必要（`requirements.txt`参照）。`test_presenter.py`の実行には不要
