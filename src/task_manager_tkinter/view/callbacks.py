"""
view.callbacks — shared mixin for View implementations
-----------------------------------------------------------
"Register and fire named callbacks" only, shared by TkTaskListFrame /
TkSettingsFrame. No tkinter dependency; mixin only, never instantiated alone.

Lives at view/ (not view/task/ or view/settings/) since it's shared across
every tab — same pattern as view/tk_main_window.py.
"""

from typing import Callable, Dict


class CallbackRegistryMixin:
    """Registers callbacks by name and fires them; no-op if none registered.

    Mix into `ttk.Frame` plus a View ABC as
    `class TkFoo(ttk.Frame, CallbackRegistryMixin, FooView)`.

    No __init__ (tkinter widget __init__s aren't cooperative) — the
    registry dict is lazily created on first access, under a name-mangled
    attribute so it can't collide with tkinter internals or a subclass.
    """

    def _set_callback(self, name: str, handler: Callable[..., object]) -> None:
        """Register a callback under the key `name` (overwrites the same key)."""
        self.__ensure_registry()[name] = handler

    def _fire(self, name: str, *args: object) -> None:
        """Call the callback registered under `name`. Does nothing if none is registered."""
        handler = self.__ensure_registry().get(name)
        if handler is not None:
            handler(*args)

    # `_x` = public API (no mangling, callable by name). `__x` (no trailing
    # `__`) = internal only, mangled to `_CallbackRegistryMixin__registry`
    # so it can't collide with ttk.Frame's or a subclass's attributes.
    def __ensure_registry(self) -> Dict[str, Callable[..., object]]:
        try:
            return self.__registry
        except AttributeError:
            self.__registry: Dict[str, Callable[..., object]] = {}
            return self.__registry
