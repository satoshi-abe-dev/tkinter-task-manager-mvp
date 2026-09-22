"""
view.callbacks — shared mixin for View implementations
-----------------------------------------------------------
Provides only "register and fire named callbacks", shared by
TkTaskListFrame / TkSettingsFrame. Has no dependency on tkinter and is
never instantiated on its own (mixin only).

It's a View-layer component shared across every feature tab (task/settings),
so it lives directly under view/ rather than view/task/ or view/settings/
(the same "layer-wide things live at the layer root" pattern as
view/tk_main_window.py).
"""

from typing import Callable, Dict


class CallbackRegistryMixin:
    """A thin mixin that just registers callbacks by name and fires them,
    silently doing nothing if none is registered.

    Meant to be mixed into ttk.Frame plus a View abstract class (TaskListView
    / SettingsView); when using it, order the class bases as
    `class TkFoo(ttk.Frame, CallbackRegistryMixin, FooView)` —
    "concrete widget -> mixin -> contract (ABC)".

    Has no __init__: tkinter widget __init__s are not cooperative, so a
    design where the mixin has an __init__ that calls super().__init__()
    is fragile to chain correctly. Instead, the registry (dict) is lazily
    created on first access.
    The attribute name self.__registry is name-mangled to
    _CallbackRegistryMixin__registry, so it never collides with tkinter's
    internals or a concrete class's own attributes.
    """

    def _set_callback(self, name: str, handler: Callable[..., object]) -> None:
        """Register a callback under the key `name` (overwrites the same key)."""
        self.__ensure_registry()[name] = handler

    def _fire(self, name: str, *args: object) -> None:
        """Call the callback registered under `name`. Does nothing if none is registered."""
        handler = self.__ensure_registry().get(name)
        if handler is not None:
            handler(*args)

    # --- How the underscore prefixes are used -------------------------------
    # Single leading `_` (_set_callback / _fire):
    #     This mixin's "public API". Concrete classes call it as
    #     self._set_callback(...). A single `_` is purely a convention with
    #     no language effect and no mangling, so it's reachable under the
    #     same name from any class.
    # Double leading `__`, no trailing `__` (__ensure_registry / __registry):
    #     Implementation details used only inside this class. `__x` inside
    #     `class C` is rewritten at compile time to `_C__x` (name mangling).
    #     That means self.__registry here is actually
    #     self._CallbackRegistryMixin__registry. Since this mixin is meant to
    #     be mixed into ttk.Frame (a tkinter class family with a large,
    #     version-dependent set of attributes) and into unknown concrete
    #     subclasses, a plain name like `_registry` could collide with their
    #     attributes down the line. Mangling with `__` guarantees a distinct
    #     slot from any other class in the inheritance tree (the goal is
    #     collision avoidance, not access restriction).
    #     Conversely, adding `__` to _set_callback / _fire — which subclasses
    #     are meant to call — would get them mangled to the calling class's
    #     name and become unreachable, which is why those use a single `_`.
    # ----------------------------------------------------------------------
    def __ensure_registry(self) -> Dict[str, Callable[..., object]]:
        try:
            return self.__registry
        except AttributeError:
            self.__registry: Dict[str, Callable[..., object]] = {}
            return self.__registry
