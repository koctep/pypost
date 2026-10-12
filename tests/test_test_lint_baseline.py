"""Strict occurrence policy and fail-closed test lint behavior (PYPOST-1303)."""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from scripts import check_test_lint_baseline as gate

pytestmark = pytest.mark.timeout(30)


@pytest.fixture
def lint_root(tmp_path: Path) -> Path:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_example.py").write_text("import math\n", encoding="utf-8")
    (tmp_path / ".flake8").write_text("[flake8]\nextend-select = T201\n", encoding="utf-8")
    return tmp_path


def _finding(root: Path) -> gate.Finding:
    return gate.parse_findings(
        "tests/test_example.py\t1\t1\tF401\t'math' imported but unused\n", root,
    )[0]


def _entry(finding: gate.Finding, count: int = 1) -> dict[str, Any]:
    path, code, message, source = finding.identity
    return {
        "path": path, "code": code, "message": [message], "source": [source],
        "count": count, "reason": "Exact legacy occurrence deferred during gate adoption.",
    }


def _baseline(root: Path, entries: list[dict[str, Any]]) -> Path:
    path = root / gate.BASELINE_NAME
    path.write_text(json.dumps({"version": 1, "entries": entries}), encoding="utf-8")
    return path


def test_cli_accepts_existing_debt_without_modifying_baseline(
    lint_root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    finding = _finding(lint_root)
    baseline = _baseline(lint_root, [_entry(finding)])
    before = baseline.read_bytes()
    monkeypatch.setattr(gate, "run_flake8", lambda _: [finding])
    assert gate.main(["--root", str(lint_root)]) == 0
    assert baseline.read_bytes() == before
    assert "1 accepted legacy occurrences" in capsys.readouterr().out


def test_duplicate_growth_fails_and_reports_only_extra_occurrence(
    lint_root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    finding = _finding(lint_root)
    _baseline(lint_root, [_entry(finding)])
    monkeypatch.setattr(gate, "run_flake8", lambda _: [finding, replace(finding, row=4)])
    assert gate.main(["--root", str(lint_root)]) == 1
    assert capsys.readouterr().out.count("F401") == 1


def test_new_source_identity_in_same_file_is_not_baselined(lint_root: Path) -> None:
    finding = _finding(lint_root)
    changed = replace(finding, source="import math as unused_math")
    new, fixed = gate.compare([changed], [_entry(finding)])
    assert new[changed.identity] == 1
    assert fixed[finding.identity] == 1


def test_f811_line_reference_and_row_changes_preserve_identity(lint_root: Path) -> None:
    finding = replace(_finding(lint_root), code="F811", message="redefinition from line 12")
    moved = replace(finding, row=30, column=5, message="redefinition from line 22")
    assert gate.compare([moved], [_entry(finding)]) == ({}, {})


def test_fixed_entries_require_explicit_pruning_and_keep_remaining_counts(
    lint_root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    finding = _finding(lint_root)
    baseline = _baseline(lint_root, [_entry(finding, count=2)])
    before = baseline.read_bytes()
    monkeypatch.setattr(gate, "run_flake8", lambda _: [finding])
    assert gate.main(["--root", str(lint_root)]) == 1
    assert "make lint-tests-prune" in capsys.readouterr().out
    assert baseline.read_bytes() == before
    assert gate.main(["--root", str(lint_root), "--prune-fixed"]) == 0
    assert gate.load_baseline(baseline) == [_entry(finding)]
    monkeypatch.setattr(gate, "run_flake8", lambda _: [])
    assert gate.main(["--root", str(lint_root), "--prune-fixed"]) == 0
    assert gate.load_baseline(baseline) == []


def test_prune_refuses_new_findings_without_writing(lint_root: Path) -> None:
    finding = _finding(lint_root)
    baseline = _baseline(lint_root, [])
    before = baseline.read_bytes()
    with pytest.raises(gate.GateError, match="refusing to prune"):
        gate.prune_baseline(baseline, [], [finding])
    assert baseline.read_bytes() == before


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("count", True), ("count", 0), ("count", -1), ("count", 1.5),
        ("reason", ""), ("reason", None), ("code", "F"),
        ("path", "pypost/example.py"), ("path", "tests/../example.py"),
        ("path", "/tests/example.py"), ("path", "tests//example.py"),
        ("path", "tests/example.txt"), ("path", "tests\\example.py"),
        ("message", []), ("message", "diagnostic"), ("message", ["\n"]),
        ("message", [" spaced "]), ("message", ["x" * 61]),
        ("source", [" import math "]), ("source", [None]), ("source", ["a\rb"]),
        ("source", ["x" * 61]),
    ],
)
def test_malformed_entry_fails(lint_root: Path, field: str, value: Any) -> None:
    entry = _entry(_finding(lint_root))
    entry[field] = value
    with pytest.raises(gate.GateError):
        gate.load_baseline(_baseline(lint_root, [entry]))


@pytest.mark.parametrize(
    "content", ["{", "null", '{"version": 2, "entries": []}',
                '{"version": true, "entries": []}', '{"version": 1, "entries": {}}',
                '{"version": 1, "version": 1, "entries": []}',
                '{"version": 1, "entries": [], "unexpected": true}'],
)
def test_malformed_schema_or_duplicate_fields_fail(lint_root: Path, content: str) -> None:
    baseline = lint_root / gate.BASELINE_NAME
    baseline.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        gate.load_baseline(baseline)


def test_duplicate_baseline_identity_and_extra_entry_fields_fail(lint_root: Path) -> None:
    entry = _entry(_finding(lint_root))
    with pytest.raises(gate.GateError, match="duplicate baseline"):
        gate.load_baseline(_baseline(lint_root, [entry, entry]))
    entry["extra"] = "not allowed"
    with pytest.raises(gate.GateError, match="entry fields"):
        gate.load_baseline(_baseline(lint_root, [entry]))


def test_missing_baseline_does_not_invoke_tool(
    lint_root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    def unexpected_scan(_: Path) -> list[gate.Finding]:
        pytest.fail("scan must not bypass missing baseline")

    monkeypatch.setattr(gate, "run_flake8", unexpected_scan)
    assert gate.main(["--root", str(lint_root)]) == 2
    assert "Test lint failed" in capsys.readouterr().err


def test_prune_replace_failure_preserves_original_and_cleans_temporary(
    lint_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = _entry(_finding(lint_root))
    baseline = _baseline(lint_root, [entry])
    before = baseline.read_bytes()

    def fail_replace(self: Path, target: Path) -> Path:
        raise OSError("simulated atomic replacement failure")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="replacement failure"):
        gate.prune_baseline(baseline, [entry], [])
    assert baseline.read_bytes() == before
    assert sorted(path.name for path in lint_root.iterdir()) == [
        ".flake8", gate.BASELINE_NAME, "tests",
    ]


@pytest.mark.parametrize(
    ("exit_code", "stdout", "stderr"),
    [(0, "unrecognized output", ""), (1, "", ""), (2, "", "tool error"),
     (0, "", "missing flake8-print plugin"), (1, "broken output", "")],
)
def test_tool_errors_or_unparseable_output_fail_closed(
    lint_root: Path, monkeypatch: pytest.MonkeyPatch, exit_code: int,
    stdout: str, stderr: str,
) -> None:
    monkeypatch.setattr(
        gate.subprocess, "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, exit_code, stdout, stderr),
    )
    with pytest.raises(gate.GateError):
        gate.run_flake8(lint_root)


def test_scan_requires_plugin_and_deadline_and_rejects_false_success(
    lint_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = "tests/test_example.py\t1\t1\tF401\t'math' imported but unused\n"

    def scan(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert "--require-plugins=flake8-print" in cmd
        assert "--jobs=1" in cmd
        assert kwargs["timeout"] == 60
        assert kwargs["cwd"] == lint_root
        return subprocess.CompletedProcess(cmd, 0, output, "")

    monkeypatch.setattr(gate.subprocess, "run", scan)
    with pytest.raises(gate.GateError, match="contradicts"):
        gate.run_flake8(lint_root)


@pytest.mark.parametrize("failure", ["timeout", "launch"])
def test_cli_reports_subprocess_failure_without_baseline_writes(
    lint_root: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], failure: str,
) -> None:
    baseline = _baseline(lint_root, [])
    before = baseline.read_bytes()

    def fail(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if failure == "timeout":
            raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])
        raise OSError("cannot launch flake8")

    monkeypatch.setattr(gate.subprocess, "run", fail)
    assert gate.main(["--root", str(lint_root), "--prune-fixed"]) == 2
    assert baseline.read_bytes() == before
    assert "Test lint failed" in capsys.readouterr().err


@pytest.mark.parametrize(
    "diagnostic", ["tests/test_example.py\t0\t1\tF401\terror",
                   "tests/test_example.py\t1\t0\tF401\terror",
                   "tests/test_example.py\t2\t1\tF401\terror",
                   "tests/missing.py\t1\t1\tF401\terror",
                   "../example.py\t1\t1\tF401\terror"],
)
def test_invalid_source_location_is_not_dropped(lint_root: Path, diagnostic: str) -> None:
    with pytest.raises((gate.GateError, OSError)):
        gate.parse_findings(diagnostic, lint_root)


def test_unreadable_source_and_escaping_symlink_fail(lint_root: Path) -> None:
    source = lint_root / "tests" / "test_example.py"
    diagnostic = "tests/test_example.py\t1\t1\tF401\terror"
    source.write_bytes(b"\xff\n")
    with pytest.raises(UnicodeError):
        gate.parse_findings(diagnostic, lint_root)
    source.unlink()
    outside = lint_root / "outside.py"
    outside.write_text("import math\n", encoding="utf-8")
    source.symlink_to(outside)
    with pytest.raises(gate.GateError, match="escapes"):
        gate.parse_findings(diagnostic, lint_root)
