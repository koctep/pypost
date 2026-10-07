"""Local verification-artifact contracts recovered by PYPOST-1077."""

from __future__ import annotations

import ast
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import pytest

from scripts.audit_dialogs_inventory import (
    DialogModule,
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


_NUMBER_WORDS = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
    "nineteen", "twenty",
)
_SCOPE_RE = re.compile(
    r"Scope: pypost/ui/dialogs/ \((\w+) (?:dialog )?modules, ([\d,]+) LOC total\)"
)
_TOTAL_RE = re.compile(r"Total: ([\d,]+) LOC")
_VERDICT_RE = re.compile(r"Individual audit complete for all (\w+) modules\.")
_STALE_CLAIMS = (
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
)
_SEMANTIC_PHRASES = (
    ("Three MCP dialogs", "executive summary must describe exactly three MCP dialogs"),
    (
        "The activity and tools dialogs are read-only",
        "executive summary must limit the read-only claim to activity and tools",
    ),
    (
        "server manager supports configuration and lifecycle changes",
        "executive summary must state the server manager mutation capability",
    ),
)


def _parse_int(text: str) -> int | None:
    """Parse ``2,505``, ``2505`` or ``**2,505**`` into an int; None when not a number."""
    digits = text.strip().strip("*").replace(",", "")
    return int(digits) if digits.isdigit() else None


def _parse_count(token: str) -> int | None:
    """Parse a module count written as digits or an English word (zero to twenty)."""
    word = token.strip().lower()
    if word in _NUMBER_WORDS:
        return _NUMBER_WORDS.index(word)
    return _parse_int(word)


def _search_normalized_lines(markdown: str, pattern: re.Pattern[str]) -> re.Match[str] | None:
    """Return the first match of ``pattern`` on a ``_normalize_prose``-d report line."""
    for line in markdown.splitlines():
        match = pattern.search(_normalize_prose(line))
        if match:
            return match
    return None


def _inventory_errors(inventory: MarkdownSection, expected: dict[str, int]) -> list[str]:
    """R2/R3 plus the inventory row sum of R4: rows against discovery."""
    rows = _parse_markdown_table(inventory.content)
    if not rows:
        return ["module inventory table must not be empty"]
    if "module" not in rows[0] or "loc" not in rows[0]:
        return ["module inventory table must contain 'Module' and 'LOC' columns"]
    errors: list[str] = []
    names = [row.get("module", "") for row in rows]
    errors.extend(
        f"module inventory missing discovered dialog module: {name}"
        for name in sorted(set(expected) - set(names))
    )
    errors.extend(
        f"module inventory lists unknown dialog module: {name}"
        for name in sorted(set(names) - set(expected))
    )
    errors.extend(
        f"module inventory lists {name} more than once"
        for name in sorted({n for n in names if names.count(n) > 1})
    )
    row_sum = 0
    for row in rows:
        name, raw = row.get("module", ""), row.get("loc", "")
        loc = _parse_int(raw)
        if loc is None or loc <= 0:
            errors.append(f"invalid LOC in inventory for {name}: {raw!r}")
            continue
        row_sum += loc
        if name in expected and loc != expected[name]:
            errors.append(f"{name}: recorded LOC {loc} != discovered LOC {expected[name]}")
    total = sum(expected.values())
    if row_sum != total:
        errors.append(f"inventory row sum: {row_sum} != discovered {total}")
    return errors


def _aggregate_errors(report_markdown: str, total: int) -> list[str]:
    """R4: Scope and Total LOC against the discovered total."""
    errors: list[str] = []
    for label, pattern, group in (
        ("scope total LOC", _SCOPE_RE, 2),
        ("Total line LOC", _TOTAL_RE, 1),
    ):
        match = _search_normalized_lines(report_markdown, pattern)
        if match is None:
            errors.append(f"audit report missing {label} statement")
            continue
        declared = _parse_int(match.group(group))
        if declared is None:
            errors.append(f"{label} unparseable: {match.group(group)!r}")
        elif declared != total:
            errors.append(f"{label}: declared {declared} != discovered {total}")
    return errors


def _module_count_errors(
    report_markdown: str, verdict: MarkdownSection | None, module_count: int
) -> list[str]:
    """R5: the Scope count token and the Verdict phrase against the discovered count."""
    errors: list[str] = []
    scope = _search_normalized_lines(report_markdown, _SCOPE_RE)
    verdict_match = _VERDICT_RE.search(_normalize_prose(verdict.content)) if verdict else None
    if verdict is not None and verdict_match is None:
        errors.append(f"verdict must state completion for all {module_count} modules")
    for label, match in (("scope module count", scope), ("verdict module count", verdict_match)):
        if match is None:
            continue
        declared = _parse_count(match.group(1))
        if declared is None:
            errors.append(f"{label} unparseable: {match.group(1)!r}")
        elif declared != module_count:
            errors.append(f"{label}: declared {declared} != discovered {module_count}")
    return errors


def _testability_errors(testability: MarkdownSection, expected: dict[str, int]) -> list[str]:
    """R6: the Testability summary covers exactly the discovered modules."""
    rows = _parse_markdown_table(testability.content)
    names = {row.get("dialog") or row.get("module", "") for row in rows}
    return [
        f"testability table missing dialog module: {name}"
        for name in sorted(set(expected) - names)
    ] + [
        f"testability table lists unknown dialog module: {name}"
        for name in sorted(names - set(expected))
    ]


def _dialog_audit_report_errors(
    report_markdown: str,
    modules: Sequence[DialogModule],
) -> list[str]:
    """Return one human-readable error per contract violation; empty list means valid.

    Every expected figure (module set, per-module LOC, total LOC, module count) is derived
    from ``modules``; nothing is pinned to a snapshot of the dialog package.
    """
    expected = {module.filename: module.total_lines for module in modules}
    sections = _parse_markdown_sections(report_markdown)
    errors = [
        f"audit report missing section: {name}"
        for name in ("module inventory", "testability summary", "executive summary", "verdict")
        if name not in sections
    ]
    inventory = sections.get("module inventory")
    if inventory:
        errors.extend(_inventory_errors(inventory, expected))
    errors.extend(_aggregate_errors(report_markdown, sum(expected.values())))
    errors.extend(_module_count_errors(report_markdown, sections.get("verdict"), len(expected)))
    testability = sections.get("testability summary")
    if testability:
        errors.extend(_testability_errors(testability, expected))

    norm_report = _normalize_prose(report_markdown)
    executive = sections.get("executive summary")
    norm_exec = _normalize_prose(executive.content) if executive else ""
    errors.extend(
        message
        for phrase, message in _SEMANTIC_PHRASES
        if phrase not in norm_exec and phrase not in norm_report
    )
    errors.extend(
        f"report retains contradictory stale claim: {claim}"
        for claim in _STALE_CLAIMS
        if claim in norm_report
    )
    return errors


def test_dialog_audit_report_has_full_discovery_and_coherent_aggregates() -> None:
    modules = discover_dialog_modules()
    report = _DIALOG_AUDIT_REPORT.read_text(encoding="utf-8")
    errors = list(check_audit_report_covers(modules))
    errors.extend(_dialog_audit_report_errors(report, modules))
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
