# mvp-pattern-sample-2

[English](README_en.md) | 日本語

Python (Tkinter) による MVP（Model-View-Presenter）デザインパターンのサンプル実装。
[mvp-pattern-sample-1](https://github.com/yanyayanyan1988/mvp-pattern-sample-1) の続編で、
「タブ付きの実務寄りなタスク管理アプリ」を題材にしている。

> ℹ️ GUIの表示言語は英語（コード内のコメント・このREADMEは日本語のまま）。

## スクリーンショット

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
    切り替わり、見出しに▲/▼で表示される。優先度・ステータスはアルファベット順ではなく、
    意味のある順序（Low→Medium→High、Not Started→...→Overdue）でソートされる。
    値が空欄のタスクは、昇順/降順にかかわらず常に末尾に来る。
  - 表の下にある「+ Add」「− Delete」ボタン（隣接して表の幅いっぱいに配置）でタスクの
    追加・削除を行う。専用の登録フォームは持たない。
    - 「+ Add」を押すと、全項目が空のタスクが1件追加され、選択状態になる。タスク名だけは
      空のままにせず「Task N」という仮の名前が入る（Nはタスクごとに振られる一意のid）。
      あとは他の行と同様に、インライン編集でタスク名・担当・期限・優先度・ステータスを埋めていく。
      既存の行のソート順は変えず、新しいタスクだけが常に末尾に追加される。
    - 「− Delete」は行が選択されている時だけ押せる（未選択時は無効化）。複数選択（Shift/Cmd
      クリック）にも対応しており、選択中の全件をまとめて削除できる。押すと確認ポップアップ
      （OS標準のアラート）が出て、「Yes」を選ぶと選択中の行を削除する。
  - 「Export」「Import」ボタン（「+ Add」ボタンの下）で、タスクをCSVファイルへの書き出し／
    CSVファイルからの読み込みができる。CSVインポートではStatusはファイルに書かれた値の
    ままインポートされ、下記の自動セットは行われない（見た目のハイライトは期限日で別途つく）。
  - 期限日(due_date)を過去の日付にインライン編集すると、その瞬間だけ自動でStatusを
    「Overdue」にする（完了(Done)のタスクは対象外）。あくまで編集した瞬間だけの一度きりの
    反映で、常時強制はしない。その後ユーザーが手動でStatusを別の値に変更すれば、次に期限日
    を編集するまではその選択が尊重される。
  - Statusを手動で「Overdue」にした行は、期限日が未来でも常に赤色でハイライトされる
    （完了(Done)のタスクは対象外）。
- **設定タブ**: 期限ハイライト（有効/無効・何日前から）を設定する。
  - 値を変更すると「Unsaved changes」と表示され、「Save Changes」を押すまで反映されない。
    ただし、ハイライトのON/OFFチェックボタン自体は例外で、切り替えた瞬間に一覧タブの
    ハイライト表示へ即座に反映される（「保存」を待たない）。
  - この設定は一覧タブの期限ハイライト（期限が近い/過ぎているタスクの行をオレンジ/赤で強調
    する機能）にそのまま使われる。完了(Done)ステータスのタスクは対象外。

タブ自体・ボタンの見た目はあえてOS標準に近いスタイル（`ttk.Notebook`/`ttk.Button`のデフォルト）のままにしている。

## フォルダ構成

```
task_manager_tkinter/
    main.py                   エントリーポイント（Model, View, Presenterと同じ階層）
    test_presenter.py         2つのPresenterの単体テスト（tkinter不要）
    Model/
        task/
            task.py             Task（データクラス）
            task_model.py       TaskModel
            csv_io.py            CSV書き出し/読み込み（tkinterに依存しない純粋なI/O）
        settings/
            settings_model.py   Settings（データクラス）/ SettingsModel
    View/
        task/
            task_list_view.py       TaskListView（抽象クラス）
            tk_task_list_frame.py   Tkinter実装（タスク一覧タブ）
        settings/
            settings_view.py        SettingsView（抽象クラス）
            tk_settings_frame.py    Tkinter実装（設定タブ）
        tk_main_window.py      Tkinter実装（2タブをまとめるウィンドウ全体）
    Presenter/
        task/
            task_list_presenter.py
        settings/
            settings_presenter.py
```

Model/View/Presenterのいずれも、タブの種類（`task`/`settings`）ごとにサブフォルダで分けている。
`View/tk_main_window.py`だけは両タブをまとめる存在なので`View/`直下に置いている。

## 各層の責務

| 層 | クラス | 責務 | 依存先 |
|---|---|---|---|
| Model | `TaskModel` | タスクの保持・追加（空欄タスクの追加を含む）・更新・削除のみ。UIのことは一切知らない。 | なし |
| Model | `SettingsModel` | 設定値の保持・更新のみ（メモリ上のみ、永続化はしない）。 | なし |
| Model | `csv_io` | タスクのCSV書き出し/読み込み。純粋なI/O関数。 | なし |
| View（抽象） | `TaskListView` / `SettingsView` | 各タブの「契約」（表示・入力取得・ハンドラ登録）を定義。 | なし |
| View（実装） | `tk_task_list_frame.py`(`TkTaskListFrame`) / `tk_settings_frame.py`(`TkSettingsFrame`) / `tk_main_window.py`(`TkMainWindow`) | 上記の抽象をTkinter（`ttk.Notebook` + 標準ウィジェット）で実装。 | 各View抽象, tkinter |
| Presenter | `TaskListPresenter` / `SettingsPresenter` | 各タブの「画面の振る舞い」のロジック。バリデーション・Model更新・一覧のソート状態管理・タスクの追加/削除/CSV入出力・期限ハイライトの判定を担う。`TaskListPresenter`は期限ハイライトの判定基準（有効/無効・何日前から）を得るため`SettingsModel`も参照する。 | 対応するModel（`TaskListPresenter`は`TaskModel`と`SettingsModel`の両方）, 対応するView（抽象のみ） |

各PresenterはそれぞれのView抽象にしか依存していないため、View側の実装を差し替えても（Tkinter／別のGUIライブラリ／テスト用のFakeViewなど）Presenterのコードは変更不要。

## データフロー（「+ Add」を押した時）

1. ユーザーが「タスク一覧」タブの「+ Add」ボタンを押す。
2. `TkTaskListFrame`に登録済みのハンドラ（`TaskListPresenter.on_add_click`）が呼ばれる。
3. Presenterが`TaskModel.add_blank_task()`を呼ぶ。Modelは全項目が空のタスクを追加し、
   採番したidを使って「Task N」という仮の名前を自動で入れる。
4. `refresh()`で一覧を最新化し、`view.select_task(task.id)`で追加した行を選択状態にする。
   このとき、既存行のソート順（ソートしていた場合はその結果）は変えず、新タスクだけを
   末尾に足す。
5. ユーザーは選択された行のセルをダブルクリックして、担当・期限・優先度・ステータスなどを
   インライン編集で埋めていく（既存タスクの編集と同じ仕組み）。

## 実行方法

`tkcalendar`（期限のカレンダー選択に使用）が必要なため、リポジトリ直下に仮想環境を作ってから実行する。
GUIを使うため、Tcl/Tkが使える環境で実行すること。

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cd task_manager_tkinter
../.venv/bin/python main.py
```

Windows（コマンドプロンプト / PowerShell）:

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

cd task_manager_tkinter
..\.venv\Scripts\python main.py
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

### Windowsでの動作について

`tkinter`/`ttk`/`tkcalendar`のみを使ったクロスプラットフォームなコードで、macOS専用のAPIには依存していないため、
Windowsでも動作するはず（開発・動作確認はmacOS上でのみ行っている）。

- python.org配布のPython Windows版インストーラーはTcl/Tkを標準で同梱しているため、`brew install python-tk@3.14`
  のような追加インストールは不要
- 上記の実行方法はWindows用のコマンドも併記した
- 設定タブの見出しに`font=("Helvetica", 10, "bold")`を指定している箇所があるが、Windowsに"Helvetica"は
  標準搭載されていない。Tkは存在しないフォント名が渡されてもエラーにはせず自動的にフォールバックするため、
  動作は止まらない（見た目のフォントが変わるのみ）
