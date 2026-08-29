"""Contract and edge lock tests for dotted safe path grammar.

Asserts grammar boundaries across standalone expressions, function call arguments,
and end-to-end template service rendering per PYPOST-1036.
"""

from typing import Any, Dict
import pytest

from pypost.core.function_expression_resolver import FunctionExpressionResolver
from pypost.core.function_registry import FunctionRegistry
from pypost.core.template_service import TemplateService

pytestmark = pytest.mark.timeout(30)


@pytest.fixture
def resolver() -> FunctionExpressionResolver:
    return FunctionExpressionResolver(FunctionRegistry())


# ---------------------------------------------------------------------------
# Test data matrices
# ---------------------------------------------------------------------------

INVALID_DOT_PATTERNS = [
    # Leading dot
    ".a",
    ".mcp.request",
    ".a.b.c",
    # Trailing dot
    "a.",
    "mcp.request.",
    "a.b.c.",
    # Consecutive dots / empty segments
    "a..b",
    "mcp..request",
    "a...b",
    "a.b..c",
    "a..b.c",
]

INVALID_CHAR_PATTERNS = [
    # Invalid characters in segments
    "a.b-c",
    "a.b$c",
    "a.b@c",
    "a.b/c",
    "a.b!c",
    # Segment starting with digit
    "a.1b",
    "a.b.2c",
    "mcp.request.1field",
]

INVALID_CHILD_UNDERSCORE_PATTERNS = [
    # Child segment starting with underscore
    "a._b",
    "mcp.request._private",
    "a.b._c",
    "a.b.c._d",
    "data._hidden.val",
    "_root._child",
    # Dunder attribute access
    "root.__dict__",
    "root.__globals__",
    "root.__class__",
    "mcp.request.__class__",
    "payload.user.__dict__",
]

ALL_INVALID_PATTERNS = (
    INVALID_DOT_PATTERNS
    + INVALID_CHAR_PATTERNS
    + INVALID_CHILD_UNDERSCORE_PATTERNS
)

VALID_SAFE_PATHS = [
    # Root identifiers with and without underscores
    "x",
    "_var",
    "mcp",
    "_ctx",
    "_a",
    # Multi-segment paths with root underscore
    "_context.field",
    "_a.b.c",
    "_root.user.name",
    # Deep navigation paths (3+ segments)
    "a.b.c",
    "a.b.c.d",
    "a.b.c.d.e.f",
    "mcp.request.param",
    "payload.user.contact.address.city",
    "response.data.items.first.id",
]

CATALOG_FUNCTIONS = [
    "urlencode",
    "md5",
    "base64",
    "to_int",
    "env",
]


# ---------------------------------------------------------------------------
# Standalone expression tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expr", ALL_INVALID_PATTERNS)
def test_standalone_invalid_dotted_paths_fail_syntax_validation(
    resolver: FunctionExpressionResolver, expr: str
) -> None:
    res = resolver.validate_expressions([expr])
    assert not res.is_valid, f"Expected {expr!r} to be invalid"
    assert res.code == "invalid_syntax"
    assert res.expression == expr


@pytest.mark.parametrize("expr", VALID_SAFE_PATHS)
def test_standalone_valid_dotted_paths_pass_validation(
    resolver: FunctionExpressionResolver, expr: str
) -> None:
    res = resolver.validate_expressions([expr])
    assert res.is_valid, f"Expected {expr!r} to be valid, got code: {res.code}"


# ---------------------------------------------------------------------------
# Function call argument tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("func", CATALOG_FUNCTIONS)
@pytest.mark.parametrize("arg", ALL_INVALID_PATTERNS)
def test_function_call_invalid_dotted_argument_fails_argument_validation(
    resolver: FunctionExpressionResolver, func: str, arg: str
) -> None:
    expr = f"{func}({arg})"
    res = resolver.validate_expressions([expr])
    assert not res.is_valid, f"Expected {expr!r} to be invalid"
    assert res.code == "invalid_argument"
    assert res.function_name == func
    assert res.expression == expr


@pytest.mark.parametrize("func", CATALOG_FUNCTIONS)
@pytest.mark.parametrize("arg", VALID_SAFE_PATHS)
def test_function_call_valid_dotted_argument_passes_validation(
    resolver: FunctionExpressionResolver, func: str, arg: str
) -> None:
    expr = f"{func}({arg})"
    res = resolver.validate_expressions([expr])
    assert res.is_valid, f"Expected {expr!r} to be valid, got code: {res.code}"


# ---------------------------------------------------------------------------
# TemplateService integration rendering tests
# ---------------------------------------------------------------------------

def test_template_service_renders_deep_path_navigation() -> None:
    svc = TemplateService()
    variables: Dict[str, Any] = {
        "payload": {
            "user": {
                "contact": {
                    "address": {
                        "city": "San Francisco"
                    }
                }
            }
        },
        "_ctx": {
            "user": {
                "role": "admin"
            }
        },
        "a": {
            "b": {
                "c": {
                    "d": {
                        "e": {
                            "f": "deep_value"
                        }
                    }
                }
            }
        }
    }

    assert svc.render_string("{{ payload.user.contact.address.city }}", variables) == "San Francisco"
    assert svc.render_string("{{ _ctx.user.role }}", variables) == "admin"
    assert svc.render_string("{{ a.b.c.d.e.f }}", variables) == "deep_value"
    assert svc.render_string("{{ urlencode(payload.user.contact.address.city) }}", variables) == "San%20Francisco"


@pytest.mark.parametrize("expr", ALL_INVALID_PATTERNS)
def test_template_service_rejects_standalone_malformed_paths(expr: str) -> None:
    svc = TemplateService()
    template = f"{{{{ {expr} }}}}"
    result = svc.render_string(template, {"data": {"val": "test"}})
    # Invalid syntax must fail validation and return raw fallback template
    assert result == template


@pytest.mark.parametrize("func", ["urlencode", "md5", "base64"])
@pytest.mark.parametrize("arg", [".mcp.request", "data.", "a..b", "data._private", "root.__dict__", "a.b-c"])
def test_template_service_rejects_function_malformed_arguments(func: str, arg: str) -> None:
    svc = TemplateService()
    template = f"{{{{ {func}({arg}) }}}}"
    result = svc.render_string(template, {"data": {"_private": "secret"}})
    # Invalid argument must fail validation and return raw fallback template
    assert result == template
