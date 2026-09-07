"""
view.callbacks — View 実装の共通mixin
--------------------------------------------
TkTaskListFrame / TkSettingsFrame が共通で使う「名前付きコールバックの登録と発火」
だけを担う。tkinter に依存せず、単体ではインスタンス化しない（mixin 専用）。

どの機能タブ(task/settings)にも属さない View 層共通の部品なので、
view/task/ や view/settings/ ではなく view/ 直下に置く
（view/tk_main_window.py と同じ「層共通は層ルート」パターン）。
"""

from typing import Callable, Dict


class CallbackRegistryMixin:
    """名前でコールバックを登録し、未登録なら黙って無視して呼び出すだけの薄いmixin。

    ttk.Frame と View 抽象クラス(TaskListView / SettingsView)に add-on する前提で、
    使うときは `class TkFoo(ttk.Frame, CallbackRegistryMixin, FooView)` のように
    「具象ウィジェット → mixin → 契約(ABC)」の順で並べる。

    __init__ を持たない: tkinter のウィジェットの __init__ は協調的(cooperative)では
    ないため、mixinが __init__ を持って super().__init__() を呼ぶ設計にすると
    連鎖が壊れやすい。代わりにレジストリ(dict)を初回アクセス時に遅延生成する。
    属性名 self.__registry は name-mangling で _CallbackRegistryMixin__registry に
    なるので、tkinter 内部や具象クラスの属性と衝突しない。
    """

    def _set_callback(self, name: str, handler: Callable[..., object]) -> None:
        """name というキーでコールバックを登録する（同じキーは上書き）。"""
        self.__ensure_registry()[name] = handler

    def _fire(self, name: str, *args: object) -> None:
        """name に登録されたコールバックを呼ぶ。未登録なら何もしない。"""
        handler = self.__ensure_registry().get(name)
        if handler is not None:
            handler(*args)

    # --- アンダースコアの使い分け --------------------------------------------
    # 先頭 `_` 1個 (_set_callback / _fire):
    #     このmixinの「公開 API」。具象クラス側で self._set_callback(...) と
    #     呼ぶ。`_` 1個は慣習だけで言語的な効果は無く、mangling もされないので、
    #     どのクラスから呼んでも同じ名前で届く。
    # 先頭 `__` 2個・末尾 `__` 無し (__ensure_registry / __registry):
    #     クラス内部だけで使う実装詳細。`class C` 内の `__x` はコンパイル時に
    #     `_C__x` へ自動書き換え (name mangling) される。つまりここの
    #     self.__registry は実体としては self._CallbackRegistryMixin__registry。
    #     このmixinは ttk.Frame（＝属性を大量に持ち、バージョンで増減する
    #     tkinter のクラス群）や未知の具象サブクラスに mixin される前提なので、
    #     `_registry` のような普通の名前だと将来それらの属性と衝突しうる。
    #     `__` で mangling させることで、継承ツリーの他クラスと確実に別スロットに
    #     なる（アクセス制限が目的ではなく、あくまで衝突回避）。
    #     逆に、サブクラスから呼ばせたい _set_callback / _fire に `__` を付けると
    #     呼び出し側クラス名で mangling されて届かなくなるため、そちらは `_` 1個。
    # ----------------------------------------------------------------------
    def __ensure_registry(self) -> Dict[str, Callable[..., object]]:
        try:
            return self.__registry
        except AttributeError:
            self.__registry: Dict[str, Callable[..., object]] = {}
            return self.__registry
