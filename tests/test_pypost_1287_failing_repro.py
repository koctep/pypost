"""Failing repro for PYPOST-1287: dialog audit inventory drift is not detected.

Before the fix, the dialog audit contract in ``tests/test_pypost_1077_verification_artifacts.py``
pinned snapshot values (nine modules, 1,790 LOC, ``mcp_servers_dialog.py`` at 486) and never
compared a row's LOC with discovery. These tests drive the live contract test through
its module-level seams (``discover_dialog_modules``, ``check_audit_report_covers`` and
``_DIALOG_AUDIT_REPORT``) with synthetic discovery and a synthetic report, and also check
the real report against real discovery.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import re

import pytest

from scripts.audit_dialogs_inventory import DialogModule
import tests.test_pypost_1077_verification_artifacts as contract


pytestmark = pytest.mark.timeout(10)

_ALPHA = "alpha_dialog.py"
_BETA = "beta_dialog.py"
_GAMMA = "gamma_dialog.py"
_GHOST = "ghost_dialog.py"


def _module(filename: str, total_lines: int) -> DialogModule:
    """Build a synthetic discovered dialog module."""
    return DialogModule(
        filename=filename,
        path=f"pypost/ui/dialogs/{filename}",
        total_lines=total_lines,
        non_empty_lines=total_lines,
    )


def _synthetic_report(
    rows: Sequence[tuple[str, int]],
    scope_count: str,
    scope_total: str,
    total_line: str,
    verdict_count: str,
) -> str:
    """Return a minimal audit report carrying every required section and phrase."""
    inventory = "\n".join(
        f"| `{name}` | {loc} | `Cls` | Responsibility | main window |" for name, loc in rows
    )
    testability = "\n".join(f"| `{name}` | Yes | Mocks |" for name, _ in rows)
    return (
        "# Synthetic Dialog SOLID Audit Report\n"
        "\n"
        "**Date:** 2026-06-11\n"
        f"**Scope:** `pypost/ui/dialogs/` ({scope_count} dialog modules, "
        f"{scope_total} LOC total)\n"
        "\n"
        "## Executive Summary\n"
        "\n"
        "**Three MCP dialogs** use injected data or callbacks. The activity and tools dialogs\n"
        "are read-only; the server manager supports configuration and lifecycle changes.\n"
        "\n"
        "## Module Inventory\n"
        "\n"
        "| Module | LOC | Class | Responsibility | Opened from |\n"
        "| --- | ---: | --- | --- | --- |\n"
        f"{inventory}\n"
        "\n"
        f"**Total:** {total_line} LOC (vs PYPOST-40 grouped ~400 LOC).\n"
        "\n"
        "## Cross-Cutting Maintainability\n"
        "\n"
        "### Testability summary\n"
        "\n"
        "| Dialog | Direct unit tests | Integration / mock coverage |\n"
        "| --- | --- | --- |\n"
        f"{testability}\n"
        "\n"
        "## Verdict\n"
        "\n"
        f"Individual audit **complete** for all {verdict_count} modules. No blockers.\n"
    )


def _install_synthetic(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    modules: list[DialogModule],
    report_markdown: str,
) -> None:
    """Point the live contract test's seams at synthetic discovery and report."""
    report_path = tmp_path / "30-dialogs-audit-report.md"
    report_path.write_text(report_markdown, encoding="utf-8")
    monkeypatch.setattr(contract, "discover_dialog_modules", lambda: list(modules))
    monkeypatch.setattr(contract, "check_audit_report_covers", lambda _modules: [])
    monkeypatch.setattr(contract, "_DIALOG_AUDIT_REPORT", report_path)


def _run_contract_expecting_failure() -> str:
    """Run the live contract test and return only its custom assertion message.

    pytest appends its rewritten ``assert not [...]`` explanation, which joins every
    error onto one line. Dropping everything from the first ``assert `` line keeps one
    error per line, so per-line matching cannot span separate errors.
    """
    with pytest.raises(AssertionError) as excinfo:
        contract.test_dialog_audit_report_has_full_discovery_and_coherent_aggregates()
    lines = str(excinfo.value).splitlines()
    custom: list[str] = []
    for line in lines:
        if line.startswith("assert "):
            break
        custom.append(line)
    return "\n".join(custom)


def _any_line_matches(message: str, pattern: str) -> bool:
    """Return True when one single line of ``message`` matches ``pattern``."""
    compiled = re.compile(pattern)
    return any(compiled.search(line) for line in message.splitlines())


def _any_line_contains(message: str, needle: str) -> bool:
    """Return True when one single line of ``message`` contains ``needle``."""
    return any(needle in line for line in message.splitlines())


def test_coherent_synthetic_report_passes_without_pinned_snapshot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Case 1: a report coherent with discovery is accepted (no pinned counts/LOC)."""
    modules = [_module(_ALPHA, 120), _module(_BETA, 80)]
    report = _synthetic_report(
        rows=[(_ALPHA, 120), (_BETA, 80)],
        scope_count="two",
        scope_total="200",
        total_line="200",
        verdict_count="two",
    )
    _install_synthetic(monkeypatch, tmp_path, modules, report)

    contract.test_dialog_audit_report_has_full_discovery_and_coherent_aggregates()


def test_per_module_loc_drift_names_module_recorded_and_discovered(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Case 2: a stale row LOC is reported with module, recorded and discovered values."""
    modules = [_module(_ALPHA, 120), _module(_BETA, 80)]
    report = _synthetic_report(
        rows=[(_ALPHA, 100), (_BETA, 80)],
        scope_count="two",
        scope_total="200",
        total_line="200",
        verdict_count="two",
    )
    _install_synthetic(monkeypatch, tmp_path, modules, report)

    message = _run_contract_expecting_failure()

    assert _any_line_matches(message, r"alpha_dialog\.py\D+\b100\b\D+\b120\b"), message


def test_missing_and_unknown_modules_are_named_individually(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Case 3: a missing discovered module and an unknown listed module are both named."""
    modules = [_module(_ALPHA, 120), _module(_BETA, 80), _module(_GAMMA, 50)]
    report = _synthetic_report(
        rows=[(_ALPHA, 120), (_BETA, 80), (_GHOST, 50)],
        scope_count="three",
        scope_total="250",
        total_line="250",
        verdict_count="three",
    )
    _install_synthetic(monkeypatch, tmp_path, modules, report)

    message = _run_contract_expecting_failure()

    assert _any_line_contains(message, _GAMMA), message
    assert _any_line_contains(message, _GHOST), message


def test_aggregate_drift_reports_declared_and_discovered_values(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Case 4: stale Scope count and Scope/Total LOC report declared vs discovered ints."""
    modules = [_module(_ALPHA, 120), _module(_BETA, 80)]
    report = _synthetic_report(
        rows=[(_ALPHA, 120), (_BETA, 80)],
        scope_count="three",
        scope_total="999",
        total_line="999",
        verdict_count="two",
    )
    _install_synthetic(monkeypatch, tmp_path, modules, report)

    message = _run_contract_expecting_failure()

    assert _any_line_matches(message, r"declared\D*\b3\b\D+discovered\D*\b2\b"), message
    assert _any_line_matches(message, r"declared\D*\b999\b\D+discovered\D*\b200\b"), message


def test_live_report_inventory_loc_matches_discovery() -> None:
    """Case 5: the real report's inventory LOC equals real discovery (actual defect)."""
    expected = {
        module.filename: module.total_lines for module in contract.discover_dialog_modules()
    }
    report = contract._DIALOG_AUDIT_REPORT.read_text(encoding="utf-8")
    sections = contract._parse_markdown_sections(report)
    assert "module inventory" in sections, "audit report missing section: module inventory"
    rows = contract._parse_markdown_table(sections["module inventory"].content)
    recorded = {
        row.get("module", ""): int(row["loc"].replace(",", ""))
        for row in rows
        if row.get("loc", "").replace(",", "").isdigit()
    }

    assert recorded == expected
