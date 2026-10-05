"""Local verification-artifact contracts recovered by PYPOST-1077."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import pytest

from scripts.audit_dialogs_inventory import (
    check_audit_report_covers,
    discover_dialog_modules,
)


pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DIALOG_AUDIT_REPORT = _REPO_ROOT / "ai-tasks" / "PYPOST-374" / "30-dialogs-audit-report.md"
_FUNCTION_REGISTRY_TEST = _REPO_ROOT / "tests" / "test_function_registry.py"
_JIRA_SMOKE_TEST = _REPO_ROOT / "tests" / "test_jira_mcp_live_smoke.py"
_ENCRYPTED_STARTUP_TEST = _REPO_ROOT / "tests" / "test_main_window_encrypted_startup.py"


@dataclass(frozen=True)
class MarkdownSection:
    title: str
    level: int
    content: str


class _SectionDict(dict[str, MarkdownSection]):
    def __getitem__(self, key: str) -> MarkdownSection:
        norm = key.strip().lower()
        if norm in self:
            return super().__getitem__(norm)
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        norm = key.strip().lower()
        if norm in self:
            return super().get(norm, default)
        return super().get(key, default)

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str) and super().__contains__(key.strip().lower()):
            return True
        return super().__contains__(key)


class _RowDict(dict[str, str]):
    def __getitem__(self, key: str) -> str:
        norm = key.strip().lower()
        if norm in self:
            return super().__getitem__(norm)
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        norm = key.strip().lower()
        if norm in self:
            return super().get(norm, default)
        return super().get(key, default)

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str) and super().__contains__(key.strip().lower()):
            return True
        return super().__contains__(key)


def _parse_markdown_sections(markdown: str) -> dict[str, MarkdownSection]:
    """Parse markdown document into sections keyed by heading title."""
    lines = markdown.splitlines()
    in_code_block = False
    headings: list[tuple[int, int, str]] = []

    heading_re = re.compile(r"^(#{1,6})\s+(.+)$")
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        match = heading_re.match(line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append((idx, level, title))

    sections = _SectionDict()
    if headings and headings[0][0] > 0:
        preamble = "\n".join(lines[: headings[0][0]])
        sections[""] = MarkdownSection(title="", level=0, content=preamble)

    for i, (line_idx, level, title) in enumerate(headings):
        start_line = line_idx + 1
        end_line = len(lines)
        for j in range(i + 1, len(headings)):
            if headings[j][1] <= level:
                end_line = headings[j][0]
                break
        content = "\n".join(lines[start_line:end_line])
        sec = MarkdownSection(title=title, level=level, content=content)
        sections[title.strip().lower()] = sec
        sections[title.strip()] = sec

    return sections


def _parse_markdown_table(table_markdown: str) -> list[dict[str, str]]:
    """Parse GFM table markdown into list of row dictionaries."""
    lines = [line.strip() for line in table_markdown.splitlines()]
    table_lines = [line for line in lines if "|" in line]
    if not table_lines:
        return []

    def _split_row(row_str: str) -> list[str]:
        s = row_str.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|"):
            s = s[:-1]
        return [c.strip() for c in s.split("|")]

    def _is_divider(cells: list[str]) -> bool:
        if not cells:
            return False
        return all(re.match(r"^:?-+:?$", c) for c in cells if c)

    headers: list[str] | None = None
    rows: list[dict[str, str]] = []

    for line in table_lines:
        cells = _split_row(line)
        if not cells or all(c == "" for c in cells):
            continue
        if headers is None:
            headers = [re.sub(r"^`|`$", "", c).strip().lower() for c in cells]
            continue
        if _is_divider(cells):
            continue

        row_dict = _RowDict()
        for idx, header in enumerate(headers):
            val = cells[idx] if idx < len(cells) else ""
            val = val.strip()
            if (
                (val.startswith("`") and val.endswith("`"))
                or (val.startswith('"') and val.endswith('"'))
                or (val.startswith("'") and val.endswith("'"))
            ) and len(val) >= 2:
                val = val[1:-1].strip()
            row_dict[header] = val
        rows.append(row_dict)

    return rows


def _normalize_prose(text: str, strip_formatting: bool = True) -> str:
    """Collapse whitespace sequences and optionally strip markdown formatting."""
    if strip_formatting:
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        text = re.sub(r"(\*\*\*|___)(.*?)\1", r"\2", text, flags=re.DOTALL)
        text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text, flags=re.DOTALL)
        text = re.sub(r"(\*|_)(.*?)\1", r"\2", text, flags=re.DOTALL)
        text = re.sub(r"`([^`]+)`", r"\1", text, flags=re.DOTALL)
    return " ".join(text.split())


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


def _section(markdown: str, heading: str, next_heading: str = "") -> str:
    """Extract section content between headings, supporting AST lookup and string slicing."""
    sections = _parse_markdown_sections(markdown)
    clean_title = heading.lstrip("#").strip()
    if clean_title in sections:
        return sections[clean_title].content
    if next_heading and heading in markdown and next_heading in markdown:
        start = markdown.index(heading) + len(heading)
        end = markdown.index(next_heading, start)
        return markdown[start:end]
    raise KeyError(f"section not found: {heading}")


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
    expected_filenames = {module.filename for module in modules}
    errors: list[str] = []

    issues = check_audit_report_covers(modules)
    if issues:
        errors.extend(issues)
    if len(modules) != 9:
        errors.append("dialog discovery must contain exactly nine modules")

    sections = _parse_markdown_sections(report)
    for required_name in (
        "module inventory",
        "testability summary",
        "executive summary",
        "verdict",
    ):
        if required_name not in sections:
            errors.append(f"audit report missing section: {required_name}")

    inventory_section = sections.get("module inventory")
    if inventory_section:
        inventory_rows = _parse_markdown_table(inventory_section.content)
        if not inventory_rows:
            errors.append("module inventory table must not be empty")
        else:
            if "module" not in inventory_rows[0] or "loc" not in inventory_rows[0]:
                errors.append("module inventory table must contain 'Module' and 'LOC' columns")

            inventory_filenames = [r.get("module", "") for r in inventory_rows]
            if set(inventory_filenames) != expected_filenames:
                errors.append("module inventory must cover every discovered dialog exactly once")
            if len(inventory_filenames) != len(set(inventory_filenames)):
                errors.append("module inventory contains duplicate dialog modules")

            loc_values: list[int] = []
            for r in inventory_rows:
                loc_str = r.get("loc", "")
                if loc_str.isdigit():
                    loc_val = int(loc_str)
                    if loc_val <= 0:
                        errors.append(f"invalid non-positive LOC in inventory: {loc_str}")
                    loc_values.append(loc_val)
                else:
                    errors.append(f"invalid non-numeric LOC in inventory: {loc_str}")

            if sum(loc_values) != 1790:
                errors.append(
                    f"module inventory LOC rows must sum to 1,790 (got {sum(loc_values)})"
                )

            if not any(
                r.get("module") == "mcp_servers_dialog.py" and r.get("loc") == "486"
                for r in inventory_rows
            ):
                errors.append("module inventory must record mcp_servers_dialog.py at 486 LOC")

    testability_section = sections.get("testability summary")
    if testability_section:
        testability_rows = _parse_markdown_table(testability_section.content)
        testability_filenames = {
            r.get("dialog") or r.get("module", "") for r in testability_rows
        }
        if testability_filenames != expected_filenames:
            errors.append(
                "testability table must have one row for each of the nine dialog modules"
            )

    norm_report = _normalize_prose(report)
    norm_exec = (
        _normalize_prose(sections["executive summary"].content)
        if "executive summary" in sections
        else ""
    )
    norm_verdict = (
        _normalize_prose(sections["verdict"].content)
        if "verdict" in sections
        else ""
    )

    if (
        "Scope: pypost/ui/dialogs/ (nine modules, 1,790 LOC total)" not in norm_report
        and "Scope: pypost/ui/dialogs/ (nine dialog modules, 1,790 LOC total)" not in norm_report
    ):
        errors.append("scope must state nine modules and 1,790 LOC")

    if "Three MCP dialogs" not in norm_exec and "Three MCP dialogs" not in norm_report:
        errors.append("executive summary must describe exactly three MCP dialogs")

    if (
        "The activity and tools dialogs are read-only" not in norm_exec
        and "The activity and tools dialogs are read-only" not in norm_report
    ):
        errors.append("executive summary must limit the read-only claim to activity and tools")

    if (
        "server manager supports configuration and lifecycle changes" not in norm_exec
        and "server manager supports configuration and lifecycle changes" not in norm_report
    ):
        errors.append("executive summary must state the server manager mutation capability")

    if (
        "Individual audit complete for all nine modules." not in norm_verdict
        and "Individual audit complete for all nine modules." not in norm_report
    ):
        errors.append("verdict must state completion for all nine modules")

    for stale_claim in (
        "seven modules",
        "eight modules",
        "923 LOC",
        "1,030 LOC",
        "1,208 LOC",
        "1,747 LOC",
        "1,747",
        "446 LOC",
        "446",
        "Two MCP read-only dialogs",
        "Three MCP read-only dialogs",
        "all seven modules",
        "all eight modules",
    ):
        if stale_claim in norm_report:
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
        "to_adf",
        "to_json_string",
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
