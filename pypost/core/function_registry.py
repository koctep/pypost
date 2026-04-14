"""
Registry for permitted Jinja template-callable functions and their implementations.
"""

from __future__ import annotations

import base64
import hashlib
from typing import Any, Callable
from urllib.parse import quote

from jinja2 import Environment


def _urlencode(value: object) -> str:
    """URL-encode a value for safe usage in paths/query."""
    return quote(str(value), safe="")


def _md5(value: object) -> str:
    """Return hex MD5 digest of the provided value."""
    raw = str(value).encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def _base64_encode(value: object) -> str:
    """Return Base64-encoded string for the provided value."""
    raw = str(value).encode("utf-8")
    return base64.b64encode(raw).decode("utf-8")


_DEFAULT_CATALOG: dict[str, Callable[..., Any]] = {
    "urlencode": _urlencode,
    "md5": _md5,
    "base64": _base64_encode,
}


class FunctionRegistry:
    """
    Single source of truth for allowed template function names and callables.

    Under normal use, TemplateService.__init__ constructs a registry and calls
    register_into_env once. register_into_env sets or replaces only the catalog
    keys on env.globals (urlencode, md5, base64); other globals are unchanged.
    Repeat calls re-bind those keys only to the registry's implementations.
    """

    def __init__(self) -> None:
        self._functions: dict[str, Callable[..., Any]] = dict(_DEFAULT_CATALOG)
        self._allowed_names: frozenset[str] = frozenset(self._functions)

    def allowed_names(self) -> frozenset[str]:
        """Immutable set of permitted function names for template expressions."""
        return self._allowed_names

    def is_allowed(self, name: str) -> bool:
        """True if name is in the catalog."""
        return name in self._functions

    def register_into_env(self, env: Environment) -> None:
        """
        Bind catalog names to callables on env.globals.

        Prefer one call from TemplateService.__init__. Repeat calls set or replace
        only catalog keys; unrelated env.globals entries are left untouched.
        """
        for name, fn in self._functions.items():
            env.globals[name] = fn

    def get(self, name: str) -> Callable[..., Any] | None:
        """
        Return the implementation for name, or None if unknown.

        Public surface for PYPOST-452 and other resolver work.
        """
        return self._functions.get(name)
