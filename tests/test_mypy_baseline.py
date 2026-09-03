"""Mypy baseline gate for pypost/core, pypost/models, and pypost/ui (PYPOST-734/815/1007)."""

from __future__ import annotations

import ast
import json
import runpy
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import scripts.check_mypy_baseline as check_mypy_baseline
from scripts.check_mypy_baseline import (
    BASELINE_PATH,
    BaselineEntry,
    MypyError,
    _diff_errors,
    _format_fixed_report,
    _format_new_report,
    _load_baseline,
    _parse_errors,
    _write_baseline,
)

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_with_mypy_paths(
    tmp_path: Path,
    paths: tuple[str, ...],
) -> dict[str, Any]:
    source_path = REPO_ROOT / "scripts/check_mypy_baseline.py"
    source = source_path.read_text(encoding="utf-8")
    assignments = [
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "MYPY_PATHS"
            for target in node.targets
        )
    ]
    assert len(assignments) == 1
    assignment_source = ast.get_source_segment(source, assignments[0])
    assert assignment_source is not None
    assert source.count(assignment_source) == 1

    temporary_module = tmp_path / "check_mypy_baseline.py"
    temporary_module.write_text(
        source.replace(assignment_source, f"MYPY_PATHS = {paths!r}"),
        encoding="utf-8",
    )
    return runpy.run_path(str(temporary_module))


class TestMypyBaseline:
    def test_mypy_timeout_fails_gate_and_reports_timeout(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        observed_timeout: list[int] = []

        def timeout_run(*args: Any, **kwargs: Any) -> None:
            del args
            observed_timeout.append(kwargs["timeout"])
            raise subprocess.TimeoutExpired(
                cmd=["python", "-m", "mypy"],
                timeout=kwargs["timeout"],
                output=b"partial stdout\n",
                stderr=b"partial stderr\n",
            )

        monkeypatch.setattr(check_mypy_baseline.subprocess, "run", timeout_run)
        monkeypatch.setattr(sys, "argv", ["check_mypy_baseline.py"])

        exit_code = check_mypy_baseline.main()
        captured = capsys.readouterr()

        assert observed_timeout == [check_mypy_baseline.MYPY_TIMEOUT_SECONDS]
        assert exit_code == 1
        assert captured.err == (
            "partial stdout\n"
            "partial stderr\n"
            "mypy timed out after 60 seconds\n"
        )
        assert "mypy baseline OK" not in captured.out

    def test_baseline_file_exists(self) -> None:
        assert BASELINE_PATH.is_file()

    def test_baseline_scope_includes_core_models_and_ui(self) -> None:
        data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        assert data["scope"] == ["pypost/core", "pypost/models", "pypost/ui"]
        assert data["error_count"] == len(data["errors"])
        assert data["error_count"] > 0
        assert data["version"] == 2

    def test_parse_errors_extracts_path_line_code_and_message(self) -> None:
        sample = (
            "pypost/core/http_client.py:218: error: Incompatible default "
            "for parameter \"variables\" [assignment]\n"
            "pypost/ui/main_window.py:42: error: Item \"None\" of "
            "\"QWidget | None\" has no attribute \"show\" [union-attr]\n"
        )
        assert _parse_errors(sample) == [
            MypyError(
                path="pypost/core/http_client.py",
                line=218,
                code="assignment",
                message='Incompatible default for parameter "variables"',
            ),
            MypyError(
                path="pypost/ui/main_window.py",
                line=42,
                code="union-attr",
                message='Item "None" of "QWidget | None" has no attribute "show"',
            ),
        ]

    def test_configured_path_extension_drives_diagnostic_parsing(
        self,
        tmp_path: Path,
    ) -> None:
        assert (REPO_ROOT / "pypost/agent").is_dir()

        module = _load_with_mypy_paths(
            tmp_path,
            (*check_mypy_baseline.MYPY_PATHS, "pypost/agent"),
        )

        agent_path = "pypost/agent/tree_index.py"
        lookalike_path = "pypost/agent_extra/check.py"
        errors = module["_parse_errors"](
            f"{agent_path}:17: error: Incompatible return value type [return-value]\n"
            f'{lookalike_path}:9: error: Name "missing" is not defined [name-defined]\n',
        )

        assert all(error.path != lookalike_path for error in errors)
        assert errors == [
            module["MypyError"](
                path=agent_path,
                line=17,
                code="return-value",
                message="Incompatible return value type",
            ),
        ], "a newly configured MYPY_PATHS entry must drive diagnostic parsing"

    def test_configured_path_alternation_escapes_and_orders_prefixes(
        self,
        tmp_path: Path,
    ) -> None:
        module = _load_with_mypy_paths(
            tmp_path,
            ("pypost/agent", "pypost/agent.ui"),
        )

        assert "(?:pypost/agent\\.ui|pypost/agent)/" in module["_ERROR_RE"].pattern
        assert module["_parse_errors"](
            "pypost/agent.ui/check.py:3: error: Specific path [assignment]\n"
            "pypost/agent/check.py:5: error: Parent path [assignment]\n"
            "pypost/agentXui/check.py:7: error: Lookalike path [assignment]\n",
        ) == [
            module["MypyError"](
                path="pypost/agent.ui/check.py",
                line=3,
                code="assignment",
                message="Specific path",
            ),
            module["MypyError"](
                path="pypost/agent/check.py",
                line=5,
                code="assignment",
                message="Parent path",
            ),
        ]

    def test_baseline_entries_use_scoped_paths(self) -> None:
        data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        for entry in data["errors"]:
            assert (
                entry["path"].startswith("pypost/core/")
                or entry["path"].startswith("pypost/models/")
                or entry["path"].startswith("pypost/ui/")
            )

    def test_gate_treats_line_shifted_error_as_unchanged(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """PYPOST-1007 red test: a baselined error that only shifts line
        number (same path, same code, same message — e.g. an unrelated
        import added above it) must NOT be reported as a new/fixed diff.

        Today's gate keys a baselined error by (path, line, code)
        (`scripts/check_mypy_baseline.py::_ERROR_RE` /
        `main()`'s set-difference over `"path:line:code"` strings), so the
        exact same logical error reappearing at a different line looks like
        one error "fixed" (old line disappears) plus one "new" error (same
        error at the new line) — a phantom diff. This test builds a
        baseline via the real `--update-baseline` flow (exercising the
        current `_write_baseline`/`_load_baseline` shape), then re-runs the
        gate against mypy output for the identical error shifted to a
        different line, and asserts the gate reports a clean pass (exit
        code 0). It fails against today's `path:line:code` key because the
        line shift makes the current gate's set diff see two distinct
        entries instead of one unchanged one.
        """
        baseline_file = tmp_path / "mypy-baseline.json"
        monkeypatch.setattr(check_mypy_baseline, "BASELINE_PATH", baseline_file)

        original_output = (
            'pypost/core/http_client.py:10: error: Incompatible default '
            'for parameter "variables" [assignment]\n'
        )
        monkeypatch.setattr(
            check_mypy_baseline,
            "_run_mypy",
            lambda: (1, original_output),
        )
        monkeypatch.setattr(sys, "argv", ["check_mypy_baseline.py", "--update-baseline"])
        assert check_mypy_baseline.main() == 0
        assert baseline_file.is_file()

        # Same file, same error code, same message — only the line number
        # shifted (simulating an unrelated import added above it).
        shifted_output = (
            'pypost/core/http_client.py:25: error: Incompatible default '
            'for parameter "variables" [assignment]\n'
        )
        monkeypatch.setattr(
            check_mypy_baseline,
            "_run_mypy",
            lambda: (1, shifted_output),
        )
        monkeypatch.setattr(sys, "argv", ["check_mypy_baseline.py"])

        exit_code = check_mypy_baseline.main()

        assert exit_code == 0, (
            "gate must not report a diff when the same (path, code, "
            "message) error merely shifts line number, but today's "
            "path:line:code key reports it as both fixed and new "
            f"(exit_code={exit_code})"
        )

    def test_gate_reports_all_baselined_errors_fixed_when_current_is_empty(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        baseline_file = tmp_path / "mypy-baseline.json"
        baseline_file.write_text(
            json.dumps(
                {
                    "version": check_mypy_baseline.BASELINE_VERSION,
                    "scope": list(check_mypy_baseline.MYPY_PATHS),
                    "error_count": 1,
                    "errors": [
                        {
                            "path": "pypost/core/client.py",
                            "code": "assignment",
                            "message": "Incompatible value",
                        },
                    ],
                },
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(check_mypy_baseline, "BASELINE_PATH", baseline_file)
        monkeypatch.setattr(check_mypy_baseline, "_run_mypy", lambda: (0, ""))
        monkeypatch.setattr(sys, "argv", ["check_mypy_baseline.py"])

        exit_code = check_mypy_baseline.main()
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "New mypy errors (not in baseline):" not in captured.err
        assert "Resolved baseline errors (update baseline):" in captured.err
        assert "- pypost/core/client.py: Incompatible value [assignment]" in captured.err
        assert "Baseline: 1 errors; current: 0 errors" in captured.err
        assert "mypy baseline OK" not in captured.out


class TestDiffErrors:
    """Unit tests for the pure `_diff_errors` multiset difference.

    All hermetic: no subprocess/mypy invocation, no filesystem I/O — data is
    constructed directly, per do-testing.md's pure-unit tier.
    """

    def test_diff_errors_empty_current_and_baseline_have_no_diff(self) -> None:
        new_keys, fixed_keys = _diff_errors([], [])

        assert new_keys == []
        assert fixed_keys == []

    def test_diff_errors_ignores_line_shift_alone(self) -> None:
        # Red test 1 (PYPOST-1007 Step 3): same (path, code, message) at two
        # different lines must produce zero new and zero fixed entries.
        current = [
            MypyError(
                path="pypost/core/http_client.py",
                line=25,
                code="assignment",
                message='Incompatible default for parameter "variables"',
            ),
        ]
        baseline = [
            BaselineEntry(
                path="pypost/core/http_client.py",
                code="assignment",
                message='Incompatible default for parameter "variables"',
            ),
        ]

        new_keys, fixed_keys = _diff_errors(current, baseline)

        assert new_keys == []
        assert fixed_keys == []

    def test_diff_errors_detects_new_error_same_line(self) -> None:
        # Red test 2 (regression guard): same path/line, different message
        # (i.e. a genuinely different error) must be reported as both fixed
        # (old identity) and new (changed identity) — dropping line from
        # the key must never mask a real change.
        current = [
            MypyError(
                path="pypost/core/http_client.py",
                line=10,
                code="assignment",
                message='Incompatible default for parameter "headers"',
            ),
        ]
        baseline = [
            BaselineEntry(
                path="pypost/core/http_client.py",
                code="assignment",
                message='Incompatible default for parameter "variables"',
            ),
        ]

        new_keys, fixed_keys = _diff_errors(current, baseline)

        assert new_keys == [
            (
                "pypost/core/http_client.py",
                "assignment",
                'Incompatible default for parameter "headers"',
            ),
        ]
        assert fixed_keys == [
            (
                "pypost/core/http_client.py",
                "assignment",
                'Incompatible default for parameter "variables"',
            ),
        ]

    def test_diff_errors_detects_fixed_error(self) -> None:
        # Red test 3: an entry present in baseline but absent from current
        # (regardless of key) is still reported as fixed.
        baseline = [
            BaselineEntry(
                path="pypost/ui/main_window.py",
                code="union-attr",
                message='Item "None" of "QWidget | None" has no attribute "show"',
            ),
        ]

        new_keys, fixed_keys = _diff_errors([], baseline)

        assert new_keys == []
        assert fixed_keys == [
            (
                "pypost/ui/main_window.py",
                "union-attr",
                'Item "None" of "QWidget | None" has no attribute "show"',
            ),
        ]

    def test_diff_errors_multiset_partial_fix(self) -> None:
        # Required: closes the blocking review gap. Baseline has 3
        # instances of an identical key; current run has 2 (1 fixed, 2
        # remain). A set-based diff would report 0 fixed since the key is
        # still present on both sides; Counter-based diffing must report
        # exactly 1 fixed and 0 new.
        key = ("pypost/ui/widgets/mixins.py", "attr-defined", '"Widget" has no attribute "foo"')
        baseline = [BaselineEntry(*key) for _ in range(3)]
        current = [
            MypyError(path=key[0], line=line, code=key[1], message=key[2])
            for line in (40, 88)
        ]

        new_keys, fixed_keys = _diff_errors(current, baseline)

        assert new_keys == []
        assert fixed_keys == [key]

    def test_diff_errors_multiset_new_duplicate(self) -> None:
        # Required companion case: baseline has 1 instance of a key,
        # current run has 2 (a duplicate appeared). A set diff would report
        # 0 new (key already "present"); Counter-based diffing must report
        # exactly 1 new and 0 fixed.
        key = ("pypost/ui/widgets/mixins.py", "attr-defined", '"Widget" has no attribute "foo"')
        baseline = [BaselineEntry(*key)]
        current = [
            MypyError(path=key[0], line=line, code=key[1], message=key[2])
            for line in (40, 88)
        ]

        new_keys, fixed_keys = _diff_errors(current, baseline)

        assert new_keys == [key]
        assert fixed_keys == []

    def test_diff_errors_multiset_full_fix(self) -> None:
        # Regression guard: baseline has 3 identical-key entries, current
        # run has 0 — must report exactly 3 fixed, not 1 (guards against
        # under-counting via an accidental set-collapse).
        key = ("pypost/ui/widgets/mixins.py", "attr-defined", '"Widget" has no attribute "foo"')
        baseline = [BaselineEntry(*key) for _ in range(3)]

        new_keys, fixed_keys = _diff_errors([], baseline)

        assert new_keys == []
        assert fixed_keys == [key, key, key]


class TestFormatReports:
    def test_format_new_report_describes_partial_change_and_sorts_lines(self) -> None:
        key = ("pypost/core/client.py", "assignment", "Incompatible value")
        current = [
            MypyError(path=key[0], line=line, code=key[1], message=key[2])
            for line in (90, 12, 45)
        ]

        report = _format_new_report([key, key], current)

        assert report == [
            "New mypy errors (not in baseline):",
            "  + pypost/core/client.py: Incompatible value [assignment]",
            "    lines: 12, 45, 90  (2 new of 3 total)",
        ]

    def test_format_new_report_omits_qualifier_for_whole_key(self) -> None:
        key = ("pypost/core/client.py", "assignment", "Incompatible value")
        current = [
            MypyError(path=key[0], line=line, code=key[1], message=key[2])
            for line in (90, 12)
        ]

        report = _format_new_report([key, key], current)

        assert report == [
            "New mypy errors (not in baseline):",
            "  + pypost/core/client.py: Incompatible value [assignment]",
            "    lines: 12, 90",
        ]

    def test_format_fixed_report_describes_partial_change(self) -> None:
        key = ("pypost/core/client.py", "assignment", "Incompatible value")
        baseline = [BaselineEntry(*key) for _ in range(3)]

        report = _format_fixed_report([key, key], baseline)

        assert report == [
            "Resolved baseline errors (update baseline):",
            "  - pypost/core/client.py: Incompatible value [assignment]"
            "  (2 of 3 baselined)",
        ]

    def test_format_fixed_report_omits_qualifier_for_whole_key(self) -> None:
        key = ("pypost/core/client.py", "assignment", "Incompatible value")
        baseline = [BaselineEntry(*key) for _ in range(2)]

        report = _format_fixed_report([key, key], baseline)

        assert report == [
            "Resolved baseline errors (update baseline):",
            "  - pypost/core/client.py: Incompatible value [assignment]",
        ]


class TestLoadBaseline:
    def test_load_baseline_rejects_legacy_flat_string_format(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        legacy_file = tmp_path / "mypy-baseline.json"
        legacy_file.write_text(
            json.dumps(
                {
                    "scope": list(check_mypy_baseline.MYPY_PATHS),
                    "error_count": 1,
                    "errors": ["pypost/core/http_client.py:10:assignment"],
                },
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(check_mypy_baseline, "BASELINE_PATH", legacy_file)

        with pytest.raises(ValueError, match="--update-baseline"):
            _load_baseline()


class TestWriteBaseline:
    def test_write_baseline_round_trip(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        baseline_file = tmp_path / "mypy-baseline.json"
        monkeypatch.setattr(check_mypy_baseline, "BASELINE_PATH", baseline_file)

        errors = [
            MypyError(
                path="pypost/core/http_client.py",
                line=10,
                code="assignment",
                message='Incompatible default for parameter "variables"',
            ),
            MypyError(
                path="pypost/ui/main_window.py",
                line=42,
                code="union-attr",
                message='Item "None" of "QWidget | None" has no attribute "show"',
            ),
        ]

        _write_baseline(errors)
        loaded = _load_baseline()

        assert {(e.path, e.code, e.message) for e in loaded} == {
            (e.path, e.code, e.message) for e in errors
        }

    def test_write_baseline_preserves_duplicate_entries(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        baseline_file = tmp_path / "mypy-baseline.json"
        monkeypatch.setattr(check_mypy_baseline, "BASELINE_PATH", baseline_file)

        errors = [
            MypyError(
                path="pypost/ui/widgets/mixins.py",
                line=40,
                code="attr-defined",
                message='"Widget" has no attribute "foo"',
            ),
            MypyError(
                path="pypost/ui/widgets/mixins.py",
                line=88,
                code="attr-defined",
                message='"Widget" has no attribute "foo"',
            ),
        ]

        _write_baseline(errors)
        data = json.loads(baseline_file.read_text(encoding="utf-8"))

        matching = [
            entry
            for entry in data["errors"]
            if entry["path"] == "pypost/ui/widgets/mixins.py"
            and entry["code"] == "attr-defined"
            and entry["message"] == '"Widget" has no attribute "foo"'
        ]
        assert len(matching) == 2
