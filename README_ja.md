# tkinter-task-manager-mvp

[English](README_en.md) | 日本語

Python (Tkinter) で作った、タブ付きのタスク管理デスクトップアプリ。
中身は MVP（Model-View-Presenter）パターンで責務を分けた実装サンプル。

> ℹ️ GUIの表示は英語。コード内コメントとこのREADMEは日本語。

> 🧭 **設計・アーキテクチャ上の判断は作者によるもの。** 主なもの:
>
> - MVPパターン（Model / View / Presenter）でのレイヤー分割と、各層の依存方向
> - フォルダ階層 ＝ クラスの import 名前空間、という命名・配置の方針
> - **GUI 全体**（画面レイアウト、OS 標準寄りのスタイル、期限ハイライトの配色、ウィンドウリサイズへの追従、tkcalendar のフォント変更）
> - **テーブルのインライン編集**（`ttk.Treeview` は本来セル編集不可。セルの矩形に Entry / Combobox を重ねて実現。期限日はカレンダーのポップアップで選ぶ）
> - データの保存方式（編集のたびに即座に DB へ保存。Save ボタンや「未保存」状態は持たない）
> - 自動バックアップ（一定間隔で `app.db` をコピー。件数ではなく「直近 24 時間」で保持）
>
> 各判断の理由は下記「[設計](#設計)」セクション、特に「[設計上の判断メモ](#設計上の判断メモ)」に書いている。実装には AI（Claude Code）をペアプログラミング相手として併用しており、その旨をコミットの `Co-Authored-By` に残している。

## スクリーンショット

| タスク一覧 | 設定 |
|---|---|
| ![タスク一覧タブ](docs/screenshots/task-list.png) | ![設定タブ](docs/screenshots/settings.png) |

---

## 使ってみる

### できること

- タスクを表で一覧表示し、セルを直接編集して管理する（専用の登録フォームは無い）
- 期限が近い／過ぎているタスクを行の色で強調する（オレンジ＝もうすぐ、赤＝超過）
- タスクを CSV に書き出し／CSV から読み込みする
- 変更は自動保存（Saveボタンは無い）。`app.db` は一定間隔で自動バックアップされる

### 動作環境

> ⚠️ **開発環境は macOS で、Windows での手動動作確認はしていない。** ただし CI（GitHub Actions）で、ロジックのテスト（`test_presenter.py`）と GUI 構築スモークテスト（`test_gui_smoke.py`）を Windows / macOS でも自動実行している。`tkinter` / `ttk` / `tkcalendar` だけのクロスプラットフォームなコードで、macOS 固有の API は使っていない。

- Python 3.14（Homebrew版）
- tkinter 利用には `brew install python-tk@3.14` が別途必要（macOS 標準の `/usr/bin` 側は非推奨の Tcl/Tk 8.5.9 のため使わない）
- GUI 起動には `tkcalendar` が必要（`requirements.txt`）。`test_presenter.py` の実行には不要
- 永続化は標準ライブラリの `sqlite3`。追加インストール不要

**Windows についての補足**

- python.org 配布の Windows インストーラーは Tcl/Tk を標準で同梱するため、`brew install python-tk@3.14` 相当の追加インストールは不要
- 設定タブの見出しに `font=("Helvetica", 10, "bold")` を指定している箇所があるが、Windows に "Helvetica" は標準搭載されていない。Tk は存在しないフォント名が渡されても自動的にフォールバックするため止まらない（見た目のフォントが変わるのみ）

### 動かす

`tkcalendar`（期限のカレンダー選択に使う）が必要なので、リポジトリ直下に仮想環境を作ってから起動する。GUIなので Tcl/Tk が使える環境で実行すること。

**macOS / Linux**

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m task_manager_tkinter.main
```

**Windows（コマンドプロンプト / PowerShell）**

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m task_manager_tkinter.main
```

`app.db` がまだ無いとき（＝初回起動）だけ `task_manager_tkinter/data/app.db`（SQLite）が作られ、デモ用のタスクが5件入る。期限日は起動日を基準に相対的に決まり、期限ハイライトが初回から「白2・黄2・赤1」に見えるようになっている。2回目以降は、全タスクを削除しても `app.db` は残るのでデモデータは復活しない。`-m` 以外の起動方法は下の「起動方法の補足」にまとめてある。

### 使い方

#### タスク一覧タブ

| やりたいこと | 操作 |
|---|---|
| 値を編集する | セルをダブルクリックしてその場で編集。優先度・ステータスはプルダウン、期限はカレンダーで選ぶ |
| 並べ替える | 列見出しをクリック。もう一度クリックで昇順⇄降順（見出しに ▲/▼）。優先度・ステータスは五十音順ではなく意味順（Low→High、Not Started→In Progress→Done）。空欄の行は常に末尾 |
| 追加する | 「+ Add」。空のタスクが末尾に増えて選択状態になる（名前だけ仮で「Task N」）。あとは他の行と同じくセルを埋めていく |
| 削除する | 行を選んで「− Delete」→ 確認ダイアログで Yes。Shift/Cmd クリックで複数選択 → まとめて削除 |
| CSV で入出力する | 「Export」／「Import」 |

期限切れの扱い:

- 期限を過ぎて未完了のタスクは自動的に赤くなる（Done は対象外）。「Overdue」という状態は無く、赤かどうかは期限日から常に計算される。期限を先の日付に直せば赤も消える。

#### 設定タブ

- **期限ハイライト**: ON/OFF と「何日前から警告するか」を設定。切り替えは即座に一覧タブへ反映される。Done のタスクは対象外。
- **バックアップ間隔**: 自動バックアップの間隔を分単位で設定（既定15分）。実行中に変えると、次にタイマーが発火したタイミングから反映される。
- 変更した値は入力した瞬間に保存される（Auto Save）。

> 💡 **動かすだけなら、ここまで読めば十分です。** この先は、このサンプルの主眼である「MVPパターンで責務をどう分けたか」の解説です。

---

## 設計

このリポジトリの主眼。MVPパターン（Model / View / Presenter）で責務をどう分けているかを解説する。

### ねらい

タブごとに別画面（タスク一覧・設定）を持つ、実務にありそうな Tkinter アプリを題材に、Model / View / Presenter で責務を分離するとどうなるかを見せるサンプル。タブ・ボタンの見た目はあえて OS 標準に近いまま（`ttk.Notebook` / `ttk.Button` のデフォルト）にしている。

### 永続化とバックアップ

タスク・設定はどちらも SQLite（標準ライブラリの `sqlite3`、追加インストール不要）に保存する。**編集は常に即座に DB へ書き込まれる**（Auto Save）。Saveボタン・「未保存」表示・終了時の確認ダイアログは無い。保存を意識しなくてよい代わりに、うっかり操作を取り消す手段も無い（下記の自動バックアップが唯一の保険）。

設定した間隔（既定15分）ごとに `app.db` の変更を検知し、変化があれば `data/backups/` へコピーする（前回のバックアップ以降に変化が無ければスキップ）。直近 **24時間** 分だけ残して古いものは自動的に削除する（件数ではなく経過時間で間引く方式）。ディスク破損などで DB ファイル自体が読めなくなった場合の備え。SQLite のトランザクションは書き込み中クラッシュには強いが、ファイルごと壊れるケースまでは守れないため。

### フォルダ構成

```
task_manager_tkinter/         ルートパッケージ（フォルダ階層 ＝ クラスの名前空間）
    main.py                   エントリーポイント（model, view, presenterと同じ階層）
    test_presenter.py         2つのPresenterの単体テスト（tkinter不要）
    data/                     SQLiteデータベース(app.db)の置き場。実行時に自動作成される
        backups/               設定した間隔(既定15分)ごとに自動作成されるapp.dbのバックアップ(直近24時間分)
    model/
        lib/                  クラスを持たない純粋I/Oモジュールの置き場
            db_path.py            DBファイルの既定パス（task/settingsで共有）
            db_backup.py          app.dbのバックアップ・世代管理（純粋なI/O）
            task_db.py            タスクの永続化(SQLite)。tkinterに依存しない純粋なI/O。
                                   save()時にメモリ上の状態をまるごと書き込む方式
            settings_db.py       設定の永続化(SQLite)。tkinterに依存しない純粋なI/O
            csv_io.py            CSV書き出し/読み込み（tkinterに依存しない純粋なI/O）
        task/
            entity.py           Task（データクラス）＋ PRIORITIES / STATUSES
            store.py            TaskModel（メモリ上のタスク集合を保持し永続化を委譲）
        settings/
            entity.py           Settings（データクラス）
            store.py            SettingsModel
    view/
        callbacks.py            CallbackRegistryMixin（両 tk_frame 共通のコールバック登録 mixin）
        task/
            contract.py         TaskListView（抽象クラス＝Presenterが依存する契約）
            tk_frame.py         Tkinter実装（タスク一覧タブ）
        settings/
            contract.py         SettingsView（抽象クラス＝Presenterが依存する契約）
            tk_frame.py         Tkinter実装（設定タブ）
        tk_main_window.py      Tkinter実装（2タブをまとめるウィンドウ全体）
    presenter/               （タブごとにファイル1個。サブフォルダは作らない）
        task.py                TaskListPresenter
        settings.py            SettingsPresenter
```

`model` / `view` では、ファイル名は**役割**（`entity` / `store` / `contract` / `tk_frame`）だけを表し、
どのタブのものかは**フォルダ**（`task` / `settings`）が示す。フォルダ名や層名（`view` など）は
ファイル名で繰り返さない。`presenter` はタブごとに1クラスしか無いのでサブフォルダを作らず、
`task.py` / `settings.py` を直下に置く。

`model` / `view` のサブフォルダはそのままクラスの import 名前空間になっている（例:
`model/task/` ⇔ `task_manager_tkinter.model.task.TaskModel`）。各サブパッケージの
`__init__.py`が公開クラスを再エクスポートしているため、利用側は所在フォルダの
ドット表記でそのまま import できる（`from task_manager_tkinter.model.task import TaskModel`）。
`presenter` は `from task_manager_tkinter.presenter.task import TaskListPresenter`
（`presenter/task.py` から直接）。

`view/tk_main_window.py`だけは両タブをまとめる存在なので`view/`直下に置いている。
`view/callbacks.py`も同様に、どの機能タブにも属さない View 層共通の mixin なので
`view/`直下に置く。`TkTaskListFrame` / `TkSettingsFrame` は
`(ttk.Frame, CallbackRegistryMixin, <contract>)` の順で多重継承し、コールバックの
登録・発火だけをこの mixin に委ねている（`__init__` を持たない mixin で、
tkinter の `super().__init__` 連鎖に干渉しない）。
`db_path.py`など**クラスを持たない純粋I/Oモジュール**は`model/lib/`にまとめている。

### 各層の責務

| 層 | クラス | 責務 | 依存先 |
|---|---|---|---|
| Model | `TaskModel` | タスクの保持・追加（空欄タスクの追加を含む）・更新・削除のドメインロジック。編集操作はメモリ上の状態だけを書き換え、`save()`が呼ばれた時だけ`task_db`へ永続化を委譲する（自身はSQLを知らない）。UIのことも一切知らない。 | `task_db` |
| Model | `SettingsModel` | 設定値の保持・更新のドメインロジック。永続化の詳細（SQLite）は`settings_db`に委譲し、自身はSQLを知らない。 | `settings_db` |
| Model | `task_db` / `settings_db`（`model/lib/`） | タスク・設定をSQLiteに保存/読み込みする。tkinterに依存しない純粋なI/O関数。 | `db_path`（DBファイルの場所） |
| Model | `db_backup` | `app.db`をタイムスタンプ付きでバックアップし、指定した保持期間（既定24時間）より古いものを削除する。純粋なI/O関数。呼び出しタイミング（`SettingsModel`で設定した間隔、既定15分）はmain.pyが管理する。 | なし |
| Model | `csv_io` | タスクのCSV書き出し/読み込み。純粋なI/O関数。 | なし |
| View（抽象） | `TaskListView` / `SettingsView` | 各タブの「契約」（表示・入力取得・ハンドラ登録）を定義。 | なし |
| View（実装） | `view/task/tk_frame.py`(`TkTaskListFrame`) / `view/settings/tk_frame.py`(`TkSettingsFrame`) / `view/tk_main_window.py`(`TkMainWindow`) | 上記の抽象をTkinter（`ttk.Notebook` + 標準ウィジェット）で実装。 | 各View抽象, tkinter |
| Presenter | `TaskListPresenter` / `SettingsPresenter` | 各タブの「画面の振る舞い」のロジック。バリデーション・Model更新・一覧のソート状態管理・タスクの追加/削除/CSV入出力・期限ハイライトの判定を担う。`refresh()`（または`on_field_changed()`）のたびに未保存の変更があればその場で`save()`する（Auto Save）。`TaskListPresenter`は期限ハイライトの判定基準（有効/無効・何日前から）を得るためにも`SettingsModel`を参照する。 | 対応するModel（`TaskListPresenter`は`TaskModel`と`SettingsModel`の両方）, 対応するView（抽象のみ） |

各 Presenter はそれぞれの View 抽象にしか依存していないため、View 実装を差し替えても（Tkinter ／ 別の GUI ライブラリ ／ テスト用の FakeView）Presenter のコードは変更不要。同様に `TaskModel` / `SettingsModel` は永続化方法を `task_db` / `settings_db` に隠しており、実際「メモリのみ」から「SQLite（即時書き込み）」へ切り替えたときも Presenter・View は一切変更しなかった（経緯は「設計上の判断メモ」）。

### データフロー（「+ Add」を押した時）

1. ユーザーが「タスク一覧」タブの「+ Add」ボタンを押す。
2. `TkTaskListFrame`に登録済みのハンドラ（`TaskListPresenter.on_add_click`）が呼ばれる。
3. Presenterが`TaskModel.add_blank_task()`を呼ぶ。Modelは全項目が空のタスクを追加し、
   採番したidを使って「Task N」という仮の名前を自動で入れる。
4. `refresh()`で一覧を最新化し、`view.select_task(task.id)`で追加した行を選択状態にする。
   このとき、既存行のソート順（ソートしていた場合はその結果）は変えず、新タスクだけを
   末尾に足す。
5. ユーザーは選択された行のセルをダブルクリックして、担当・期限・優先度・ステータスなどを
   インライン編集で埋めていく（既存タスクの編集と同じ仕組み）。

### 設計上の判断メモ

- **Auto Save に落ち着くまで**: 最初は「メモリのみ」→「SQLite に即時書き込み」。その後「保存前の誤操作をアプリ再起動だけで取り消せるように」と、明示的な `save()` を待つ方式（Saveボタン・未保存表示・終了時確認つき）にしたこともあった。だが「Saveボタンの置き場所に悩むくらいなら自動保存でいい」となり、今の常時 Auto Save に戻した。取り消し手段をあきらめる代わりに、定期バックアップを別の防御層として残している。この一連で Presenter・View を触ったのは「ユーザーから見える振る舞い（Saveボタン等）」が増減した時だけで、永続化方式そのものの差し替え（メモリ→SQLite）では Presenter・View は無変更だった。
- **バックアップは時間ベース保持**: 「直近 N 件」ではなく「直近 24 時間」。将来バックアップ間隔を変えても（15分→1分など）コードを直さず「1日分は遡れる」という要件が保たれる。
- **「Overdue」は状態ではなく導出**: Status は Not Started / In Progress / Done のみ。期限切れの赤は「`due_date` が今日より前 かつ Done でない」から毎回計算する。以前は手動／自動で `status="Overdue"` を保存できたが、「一度赤くなると期限を先に直しても赤のまま」という戻れない状態になったため、保存される Overdue を廃止した。

### 起動方法の補足

`-m` でもファイル指定でも起動できる。`main.py` / `test_presenter.py` は先頭で `__package__` 未設定（＝スクリプトとして直接実行された）を検知したときだけ、リポジトリのルートを `sys.path` に足すので、どちらの呼び方でも同じ絶対 import が通る。

```bash
# リポジトリのルート（task_manager_tkinter/ の親）で
.venv/bin/python -m task_manager_tkinter.main
.venv/bin/python task_manager_tkinter/main.py
cd task_manager_tkinter && ../.venv/bin/python main.py
```

Windows:

```bat
.venv\Scripts\python -m task_manager_tkinter.main
.venv\Scripts\python task_manager_tkinter\main.py
```

### テスト

FakeView（各 View 抽象クラスの偽実装）を差し込むことで、Tkinter を一切起動せずに 2 つの Presenter のロジックを検証する。`test_presenter.py` は `view.*` パッケージ（抽象クラス `TaskListView` / `SettingsView`）だけに依存し、Tkinter 実装（`view/task/tk_frame.py` / `view/settings/tk_frame.py` / `view/tk_main_window.py`）は読み込まないので、tkinter が入っていない環境でも実行できる（`view/` 配下の `__init__.py` は抽象クラスだけを再エクスポートし、Tk 実装は巻き込まない）。`TaskModel` / `SettingsModel` は `db_path=":memory:"` でインメモリ SQLite にして、ディスクに何も残さず、テストどうしで状態が混ざらないようにしている。

```bash
# リポジトリのルートで（どちらでも可）
python3 -m task_manager_tkinter.test_presenter
python3 task_manager_tkinter/test_presenter.py
```

もう1つ、`test_gui_smoke.py` は逆に、実物の `TkMainWindow`（＝全 Tkinter ウィジェット）を生成して**例外なく組み上がることだけ**を確認する（挙動は検証しない。`mainloop()` は呼ばないのでハングしない）。画面が無い環境では自動でスキップして正常終了する。

```bash
python3 -m task_manager_tkinter.test_gui_smoke
```

CI（`.github/workflows/test.yml`）では、PR 作成時・`main` への push 時に
`test_presenter.py` を **ubuntu / Windows** で、`test_gui_smoke.py` を **Windows / macOS** で自動実行する。
