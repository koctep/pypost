"""PYPOST-1343: type-preserving ``to_json`` template helper (failing repro / contract)."""

from __future__ import annotations

import json

import pytest

from pypost.core.function_registry import FunctionRegistry
from pypost.core.json_string import to_json_string


pytestmark = pytest.mark.timeout(30)


def test_function_registry_includes_to_json():
    """``to_json`` must be in the default allow-list for Jinja templates."""
    reg = FunctionRegistry()
    assert "to_json" in reg.allowed_names(), (
        "FunctionRegistry must register to_json for type-preserving JSON bodies"
    )
    fn = reg.get("to_json")
    assert callable(fn), "to_json must be a callable in the registry"


def test_to_json_preserves_list_dict_bool_number():
    """``to_json`` must emit native JSON types, not stringified forms."""
    from pypost.core.json_string import to_json

    assert json.loads(to_json([1, True, "a"])) == [1, True, "a"]
    assert json.loads(to_json({"k": False, "n": 3})) == {"k": False, "n": 3}
    assert json.loads(to_json(True)) is True
    assert json.loads(to_json(False)) is False
    assert json.loads(to_json(3)) == 3
    assert json.loads(to_json(2.5)) == 2.5
    assert json.loads(to_json(None)) is None
    assert json.loads(to_json("quote\"me")) == 'quote"me'


def test_to_json_string_still_stringifies_list():
    """``to_json_string`` remains a JSON string literal (compatibility lock)."""
    rendered = to_json_string([1, 2])
    assert isinstance(json.loads(rendered), str), (
        f"to_json_string must still stringify non-strings: {rendered!r}"
    )
