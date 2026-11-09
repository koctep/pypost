"""Red repro for the missing shared header-selector prefix (PYPOST-1538).

The three recognition sites still spell ``header:`` privately. This test
requires each of them to call ``header_selector_name`` and then checks that
validation, selection, and sanitization follow one patched prefix. The helper
module is imported with ``importlib`` only after those structural assertions,
so a missing module is not a collection error.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from pypost.core.field_selector_syntax import validate_field_selector
from pypost.core.json_selector_engine import JsonSelectorEngine
from pypost.core.sensitive_text_sanitizer import HIDDEN_PLACEHOLDER, sanitize_headers

pytestmark = pytest.mark.timeout(30)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HELPER_MODULE = "pypost.core.header_selector_prefix"
_HELPER_PATH = f"{_HELPER_MODULE}.header_selector_name"
_EMPTY_HEADER_NAME_MESSAGE = (
    "Header selector requires a non-empty name after 'header:'. "
    "This form is not accepted."
)
_HEADER_RE_ATTRS = frozenset({"compile", "match", "search", "fullmatch"})
_COMPILED_RE_ATTRS = frozenset({"match", "search", "fullmatch"})

# label, source path, live function. The path is read only after the call check.
_CALL_SITES: tuple[tuple[str, str, Callable[..., Any]], ...] = (
    (
        "validate_field_selector",
        "pypost/core/field_selector_syntax.py",
        validate_field_selector,
    ),
    (
        "JsonSelectorEngine._compile",
        "pypost/core/json_selector_engine.py",
        JsonSelectorEngine._compile,
    ),
    (
        "sanitize_headers",
        "pypost/core/sensitive_text_sanitizer.py",
        sanitize_headers,
    ),
)


def test_three_call_sites_use_one_header_selector_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Three sites must call one helper and follow one patched prefix."""
    missing = [
        label
        for label, _relative, function in _CALL_SITES
        if not _source_calls_header_selector_name(function)
    ]
    assert not missing, f"{', '.join(missing)} do not call header_selector_name"

    sites = _load_sites()
    unbound = _calls_missing_helper_module(sites)
    assert not unbound, (
        "header_selector_name is not reached through "
        f"{_HELPER_MODULE}: " + "; ".join(unbound)
    )
    private = _private_header_recognizers(sites)
    assert not private, (
        "private header recognizer still present: " + "; ".join(private)
    )

    prefix_module = importlib.import_module(_HELPER_MODULE)
    monkeypatch.setattr(prefix_module, "HEADER_SELECTOR_PREFIX", "hdr:")
    assert prefix_module.header_selector_name("hdr:X-Custom-Secret") == "X-Custom-Secret"
    assert prefix_module.header_selector_name("HdR:X-Custom-Secret") == "X-Custom-Secret"
    assert prefix_module.header_selector_name("header:X-Custom-Secret") is None

    accepted = validate_field_selector("hdr:X-Custom-Secret")
    assert accepted.ok is True
    accepted_mixed_case = validate_field_selector("HdR:X-Custom-Secret")
    assert accepted_mixed_case.ok is True
    empty_name = validate_field_selector("hdr:")
    assert empty_name.ok is False
    assert empty_name.message == _EMPTY_HEADER_NAME_MESSAGE
    rejected = validate_field_selector("header:X-Custom-Secret")
    assert rejected.ok is False

    skipped = JsonSelectorEngine(["hdr:X-Custom-Secret"])
    assert skipped.matches([], "hdr:X-Custom-Secret") is False
    compiled = JsonSelectorEngine(["header:X-Custom-Secret"])
    assert compiled.matches([], "header:X-Custom-Secret") is True

    headers = {"X-Custom-Secret": "visible-secret"}
    hidden = sanitize_headers(headers, hidden_response_fields=["hdr:X-Custom-Secret"])
    assert hidden["X-Custom-Secret"] == HIDDEN_PLACEHOLDER
    hidden_mixed_case = sanitize_headers(
        headers,
        hidden_response_fields=["HdR:X-Custom-Secret"],
    )
    assert hidden_mixed_case["X-Custom-Secret"] == HIDDEN_PLACEHOLDER
    visible = sanitize_headers(
        headers,
        hidden_response_fields=["header:X-Custom-Secret"],
    )
    assert visible["X-Custom-Secret"] == "visible-secret"


def _source_calls_header_selector_name(function: Callable[..., Any]) -> bool:
    """Return whether the function source contains a call to the helper."""
    source = textwrap.dedent(inspect.getsource(function))
    tree = ast.parse(source)
    return any(_is_helper_call(node) for node in ast.walk(tree))


def _is_helper_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and _callee_name(node.func) == "header_selector_name"


def _callee_name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


class _Site:
    """One recognition function and the module AST that defines it."""

    def __init__(
        self,
        label: str,
        module: ast.Module,
        module_name: str,
        function: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        self.label = label
        self.module = module
        self.module_name = module_name
        self.function = function


def _load_sites() -> tuple[_Site, ...]:
    loaded: list[_Site] = []
    for label, relative, _function in _CALL_SITES:
        path = _REPO_ROOT / relative
        source = path.read_text(encoding="utf-8")
        module = ast.parse(source, filename=str(path))
        module_name = ".".join(Path(relative).with_suffix("").parts)
        loaded.append(_Site(label, module, module_name, _find_function(module, label)))
    return tuple(loaded)


def _find_function(
    module: ast.Module,
    qualname: str,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    class_name, separator, func_name = qualname.rpartition(".")
    statements: list[ast.stmt]
    if separator:
        statements = _class_body(module, class_name)
    else:
        statements = module.body
    for stmt in statements:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == func_name:
            return stmt
    raise AssertionError(f"could not find {qualname}")


def _class_body(module: ast.Module, class_name: str) -> list[ast.stmt]:
    for stmt in module.body:
        if isinstance(stmt, ast.ClassDef) and stmt.name == class_name:
            return stmt.body
    return []


def _calls_missing_helper_module(sites: tuple[_Site, ...]) -> list[str]:
    missing: list[str] = []
    for site in sites:
        paths = _import_paths(site.module.body, site.module_name)
        class_name, separator, _func_name = site.label.rpartition(".")
        if separator:
            class_paths = _import_paths(_class_body(site.module, class_name), site.module_name)
            paths.update(class_paths)
        paths.update(_import_paths(site.function.body, site.module_name))
        for call in _helper_calls(site.function):
            if not _call_reaches_helper(call, site.function, paths):
                missing.append(site.label)
                break
    return missing


def _helper_calls(function: ast.AST) -> list[ast.Call]:
    return [node for node in ast.walk(function) if _is_helper_call(node)]


def _call_reaches_helper(
    call: ast.Call,
    function: ast.AST,
    paths: dict[str, str],
) -> bool:
    func = call.func
    if isinstance(func, ast.Name):
        if _name_is_rebound(function, func.id):
            return False
        return paths.get(func.id) == _HELPER_PATH
    if isinstance(func, ast.Attribute):
        return _resolve_expr(func.value, paths) == _HELPER_MODULE
    return False


def _name_is_rebound(function: ast.AST, name: str) -> bool:
    for node in ast.walk(function):
        if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Store):
            return True
        if isinstance(node, ast.arg) and node.arg == name:
            return True
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node is not function
            and node.name == name
        ):
            return True
    return False


def _resolve_expr(expr: ast.expr, paths: dict[str, str]) -> str | None:
    if isinstance(expr, ast.Name):
        return paths.get(expr.id)
    if isinstance(expr, ast.Attribute):
        base = _resolve_expr(expr.value, paths)
        if base is None:
            return None
        return f"{base}.{expr.attr}"
    return None


def _import_paths(body: list[ast.stmt], importer: str) -> dict[str, str]:
    paths: dict[str, str] = {}
    _collect_imports(body, importer, paths)
    return paths


def _collect_imports(body: list[ast.stmt], importer: str, paths: dict[str, str]) -> None:
    for stmt in body:
        if isinstance(stmt, ast.Import):
            _bind_import(stmt, paths)
        elif isinstance(stmt, ast.ImportFrom):
            _bind_import_from(stmt, importer, paths)
        elif isinstance(stmt, ast.If):
            _collect_imports(stmt.body, importer, paths)
            _collect_imports(stmt.orelse, importer, paths)
        elif isinstance(stmt, ast.Try):
            _collect_imports(stmt.body, importer, paths)
            for handler in stmt.handlers:
                _collect_imports(handler.body, importer, paths)
            _collect_imports(stmt.orelse, importer, paths)
            _collect_imports(stmt.finalbody, importer, paths)
        elif isinstance(stmt, (ast.With, ast.AsyncWith, ast.For, ast.AsyncFor, ast.While)):
            _collect_imports(stmt.body, importer, paths)
            orelse = getattr(stmt, "orelse", [])
            _collect_imports(orelse, importer, paths)


def _bind_import(stmt: ast.Import, paths: dict[str, str]) -> None:
    for alias in stmt.names:
        if alias.asname:
            paths[alias.asname] = alias.name
        else:
            root = alias.name.split(".", 1)[0]
            paths[root] = root


def _bind_import_from(stmt: ast.ImportFrom, importer: str, paths: dict[str, str]) -> None:
    base = _resolve_import_from(stmt, importer)
    if base is None:
        return
    for alias in stmt.names:
        if alias.name == "*":
            continue
        local = alias.asname or alias.name
        paths[local] = f"{base}.{alias.name}"


def _resolve_import_from(stmt: ast.ImportFrom, importer: str) -> str | None:
    if stmt.level == 0:
        return stmt.module
    package = importer.split(".")[:-1]
    parent_hops = stmt.level - 1
    if parent_hops > len(package):
        return None
    kept = package[: len(package) - parent_hops] if parent_hops else package
    if stmt.module:
        return ".".join((*kept, stmt.module))
    return ".".join(kept)


def _private_header_recognizers(sites: tuple[_Site, ...]) -> list[str]:
    """Recognition operands only. Suggestion and error strings are not operands."""
    found: list[str] = []
    for site in sites:
        strings = _string_values(site.module, site.function)
        patterns = _compiled_header_patterns(site.module, site.function)
        for node in ast.walk(site.function):
            if isinstance(node, ast.Call):
                found.extend(_call_recognizers(site.label, node, strings, patterns))
            elif isinstance(node, ast.Subscript) and _slice_bound_is_seven(node):
                found.append(f"{site.label} slices a selector with integer bound 7")
    return found


def _call_recognizers(
    label: str,
    call: ast.Call,
    strings: dict[str, str],
    patterns: dict[str, str],
) -> list[str]:
    found: list[str] = []
    func = call.func
    if (
        isinstance(func, ast.Attribute)
        and func.attr == "startswith"
        and call.args
        and _startswith_arg_is_string(call.args[0], strings)
    ):
        found.append(f"{label} uses startswith with a string constant")
    if _call_header_pattern(call, patterns) is not None:
        found.append(f"{label} uses a regex pattern that encodes header:")
    return found


def _startswith_arg_is_string(arg: ast.expr, strings: dict[str, str]) -> bool:
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return True
    return isinstance(arg, ast.Name) and arg.id in strings


def _call_header_pattern(call: ast.Call, patterns: dict[str, str]) -> str | None:
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None
    if isinstance(func.value, ast.Name) and func.value.id == "re":
        if func.attr not in _HEADER_RE_ATTRS or not call.args:
            return None
        return _header_pattern_text(call.args[0])
    if isinstance(func.value, ast.Name) and func.attr in _COMPILED_RE_ATTRS:
        return patterns.get(func.value.id)
    if func.attr in _COMPILED_RE_ATTRS:
        pattern = _re_compile_pattern(func.value)
        if pattern is not None and _encodes_header_prefix(pattern):
            return pattern
    return None


def _header_pattern_text(expr: ast.expr) -> str | None:
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        if _encodes_header_prefix(expr.value):
            return expr.value
    return None


def _encodes_header_prefix(pattern: str) -> bool:
    return "header:" in pattern.lower()


def _string_values(module: ast.Module, function: ast.AST) -> dict[str, str]:
    pairs = _assign_pairs(module.body)
    pairs.extend(_assign_pairs_in(function))
    values: dict[str, str] = {}
    for name, expr in pairs:
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            values[name] = expr.value
    changed = True
    while changed:
        changed = False
        for name, expr in pairs:
            if isinstance(expr, ast.Name) and expr.id in values and name not in values:
                values[name] = values[expr.id]
                changed = True
    return values


def _compiled_header_patterns(module: ast.Module, function: ast.AST) -> dict[str, str]:
    pairs = _assign_pairs(module.body)
    pairs.extend(_assign_pairs_in(function))
    patterns: dict[str, str] = {}
    for name, expr in pairs:
        pattern = _re_compile_pattern(expr)
        if pattern is not None and _encodes_header_prefix(pattern):
            patterns[name] = pattern
    return patterns


def _assign_pairs(body: list[ast.stmt]) -> list[tuple[str, ast.expr]]:
    pairs: list[tuple[str, ast.expr]] = []
    for stmt in body:
        pairs.extend(_pairs_from_assign(stmt))
    return pairs


def _assign_pairs_in(tree: ast.AST) -> list[tuple[str, ast.expr]]:
    pairs: list[tuple[str, ast.expr]] = []
    for node in ast.walk(tree):
        pairs.extend(_pairs_from_assign(node))
    return pairs


def _pairs_from_assign(node: ast.AST) -> list[tuple[str, ast.expr]]:
    if isinstance(node, ast.Assign):
        return [
            (target.id, node.value)
            for target in node.targets
            if isinstance(target, ast.Name)
        ]
    if (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.value is not None
    ):
        return [(node.target.id, node.value)]
    return []


def _re_compile_pattern(expr: ast.expr) -> str | None:
    if not isinstance(expr, ast.Call) or not expr.args:
        return None
    func = expr.func
    if not (
        isinstance(func, ast.Attribute)
        and func.attr == "compile"
        and isinstance(func.value, ast.Name)
        and func.value.id == "re"
    ):
        return None
    arg = expr.args[0]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value
    return None


def _slice_bound_is_seven(node: ast.Subscript) -> bool:
    if not isinstance(node.slice, ast.Slice):
        return False
    return _is_int_seven(node.slice.lower) or _is_int_seven(node.slice.upper)


def _is_int_seven(node: ast.expr | None) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
        and node.value == 7
    )
