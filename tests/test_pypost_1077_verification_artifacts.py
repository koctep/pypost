"""Local verification-artifact contracts recovered by PYPOST-1077."""

from __future__ import annotations

import ast
from pathlib import Path
import re

import pytest

from scripts.audit_dialogs_inventory import (
    check_audit_report_covers,
    discover_dialog_modules,
    total_loc,
)


pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DIALOG_AUDIT_REPORT = _REPO_ROOT / "ai-tasks" / "PYPOST-374" / "30-dialogs-audit-report.md"
_FUNCTION_REGISTRY_TEST = _REPO_ROOT / "tests" / "test_function_registry.py"
_JIRA_SMOKE_TEST = _REPO_ROOT / "tests" / "test_jira_mcp_live_smoke.py"
_ENCRYPTED_STARTUP_TEST = _REPO_ROOT / "tests" / "test_main_window_encrypted_startup.py"


def _parse_python(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _find_function(tree: ast.AST, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"missing function {name}")


def _find_class(tree: ast.AST, name: str) -> ast.ClassDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise AssertionError(f"missing class {name}")


def _find_assignment_value(tree: ast.Module, name: str) -> ast.expr:
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in statement.targets
        ):
            return statement.value
    raise AssertionError(f"missing assignment {name}")


def _section(markdown: str, heading: str, next_heading: str) -> str:
    start = markdown.index(heading) + len(heading)
    end = markdown.index(next_heading, start)
    return markdown[start:end]


def _frozenset_values(node: ast.expr) -> set[str] | None:
    if (
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id != "frozenset"
        or len(node.args) != 1
    ):
        return None
    values = ast.literal_eval(node.args[0])
    if not isinstance(values, set) or not all(isinstance(value, str) for value in values):
        return None
    return values


def test_dialog_audit_report_has_full_discovery_and_coherent_aggregates() -> None:
    modules = discover_dialog_modules()
    report = _DIALOG_AUDIT_REPORT.read_text(encoding="utf-8")
    inventory = _section(report, "## Module Inventory", "## SOLID Assessment by Dialog")
    testability = _section(report, "### Testability summary", "### Coupling")
    inventory_rows = re.findall(r"^\| `([^`]+)` \| (\d+) \|", inventory, re.MULTILINE)
    testability_rows = re.findall(r"^\| `([^`]+)` \|", testability, re.MULTILINE)
    expected_filenames = {module.filename for module in modules}
    expected_inventory = {(module.filename, str(module.total_lines)) for module in modules}
    errors: list[str] = []

    issues = check_audit_report_covers(modules)
    if issues:
        errors.extend(issues)
    if len(modules) != 9 or total_loc(modules) != 1747:
        errors.append("dialog discovery must contain exactly nine modules totaling 1,747 LOC")
    if not any(
        module.filename == "mcp_servers_dialog.py" and module.total_lines == 446
        for module in modules
    ):
        errors.append("dialog discovery must include mcp_servers_dialog.py at 446 LOC")
    if "**Scope:** `pypost/ui/dialogs/` (nine modules, 1,747 LOC total)" not in report:
        errors.append("scope must state nine modules and 1,747 LOC")
    if set(inventory_rows) != expected_inventory:
        errors.append("module inventory must exactly match discovered filenames and LOC")
    if expected_filenames != {filename for filename, _ in inventory_rows}:
        errors.append("module inventory must cover every discovered dialog exactly once")
    if "**Three MCP dialogs**" not in report:
        errors.append("executive summary must describe exactly three MCP dialogs")
    if "The activity and tools dialogs\nare read-only" not in report:
        errors.append("executive summary must limit the read-only claim to activity and tools")
    if "server manager supports configuration and lifecycle changes" not in report:
        errors.append("executive summary must state the server manager mutation capability")
    if set(testability_rows) != expected_filenames:
        errors.append("testability table must have one row for each of the nine dialog modules")
    if "Individual audit **complete** for all nine modules." not in report:
        errors.append("verdict must state completion for all nine modules")
    for stale_claim in (
        "seven modules",
        "eight modules",
        "923 LOC",
        "1,030 LOC",
        "1,208 LOC",
        "**Two MCP read-only dialogs**",
        "**Three MCP read-only dialogs**",
        "all seven modules",
        "all eight modules",
    ):
        if stale_claim in report:
            errors.append(f"report retains contradictory stale claim: {stale_claim}")

    assert not errors, "\n".join(errors)


def test_function_catalog_expectation_is_the_exact_catalog_frozenset() -> None:
    method = _find_function(
        _parse_python(_FUNCTION_REGISTRY_TEST),
        "test_allowed_names_matches_catalog",
    )
    assertions = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "assertEqual"
        and len(node.args) == 2
        and isinstance(node.args[1], ast.Call)
    ]
    assert len(assertions) == 1
    assert _frozenset_values(assertions[0].args[1]) == {
        "urlencode",
        "md5",
        "base64",
        "to_int",
        "env",
    }


def test_jira_smoke_board_contract_and_invocation_are_exact_and_offline() -> None:
    tree = _parse_python(_JIRA_SMOKE_TEST)
    contracts = _find_assignment_value(tree, "_SMOKE_READ_ONLY_CONTRACTS")
    assert isinstance(contracts, ast.Tuple)
    board_contracts = [
        contract
        for contract in contracts.elts
        if isinstance(contract, ast.Tuple)
        and isinstance(contract.elts[0], ast.Constant)
        and contract.elts[0].value == "jira-list-boards"
    ]
    assert len(board_contracts) == 1
    board_contract = board_contracts[0]
    errors: list[str] = []
    if len(board_contract.elts) != 6:
        errors.append("jira-list-boards contract must have six declaration fields")
    elif _frozenset_values(board_contract.elts[4]) != {"maxResults", "startAt"}:
        errors.append("jira-list-boards must declare exactly maxResults and startAt inputs")

    live_smoke = _find_function(tree, "_run_live_smoke")
    board_calls = [
        node
        for node in ast.walk(live_smoke)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_mcp_call_tool_result"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Subscript)
        and isinstance(node.args[1].value, ast.Name)
        and node.args[1].value.id == "_SMOKE_TOOL_NAMES"
        and isinstance(node.args[1].slice, ast.Constant)
        and node.args[1].slice.value == 3
    ]
    assert len(board_calls) == 1
    if len(board_calls[0].args) != 3:
        errors.append("jira-list-boards must pass an explicit deterministic argument dictionary")
    elif ast.literal_eval(board_calls[0].args[2]) != {"maxResults": 50, "startAt": 0}:
        errors.append("jira-list-boards arguments must be maxResults=50 and startAt=0")

    assert not errors, "\n".join(errors)


def test_deferred_environment_presenter_has_the_mcp_controller_seam() -> None:
    presenter = _find_class(_parse_python(_ENCRYPTED_STARTUP_TEST), "_DeferredEnvPresenter")
    method_names = [
        statement.name
        for statement in presenter.body
        if isinstance(statement, ast.FunctionDef)
    ]
    assert "set_mcp_server_controller" not in method_names

    init_method = _find_function(presenter, "__init__")
    mcp_controls_assigns = [
        statement
        for statement in init_method.body
        if isinstance(statement, ast.Assign)
        and any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == "mcp_controls"
            for target in statement.targets
        )
    ]
    assert len(mcp_controls_assigns) == 1
