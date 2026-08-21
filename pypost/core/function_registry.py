"""
Registry for permitted Jinja template-callable functions and their implementations.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
from typing import Any, Callable
from urllib.parse import quote

from jinja2 import Environment

from pypost.core.template_expression_types import IntegerConversionError


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


def _to_int(value: object) -> int:
    """Accept a true integer or convert an ASCII decimal string without coercion."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and re.fullmatch(r"[+-]?[0-9]+", value):
        return int(value)
    raise IntegerConversionError("to_int requires a native integer or ASCII decimal string")


def _env(name: object) -> str:
    """Return operating system environment variable value, or empty string if unset."""
    if hasattr(name, "_undefined_name") and getattr(name, "_undefined_name"):
        key_name = getattr(name, "_undefined_name")
    else:
        key_name = str(name)
    return os.environ.get(key_name, "")


_DEFAULT_CATALOG: dict[str, Callable[..., Any]] = {
    "urlencode": _urlencode,
    "md5": _md5,
    "base64": _base64_encode,
    "to_int": _to_int,
    "env": _env,
}


class FunctionRegistry:
    """Single source of truth for allowed template function names and callables."""

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

        Under normal use, TemplateService.__init__ constructs a registry and calls
        this once. Sets or replaces only catalog keys (urlencode, md5, base64);
        other globals are unchanged. Repeat calls re-bind those keys only to the
        registry's implementations.
        """
        for name, fn in self._functions.items():
            env.globals[name] = fn

    def get(self, name: str) -> Callable[..., Any] | None:
        """
        Return the implementation for name, or None if unknown.

        Public surface for PYPOST-452 and other resolver work.
        """
        return self._functions.get(name)
