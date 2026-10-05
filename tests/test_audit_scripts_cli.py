"""Dedicated unit tests for audit scripts CLI argument parsing and error handling."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

pytestmark = pytest.mark.timeout(30)

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load_script_module(name: str, path: Path) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_baseline_metrics = _load_script_module(
    "audit_baseline_metrics",
    _SCRIPTS_DIR / "audit_baseline_metrics.py",
)
_dialogs_inventory = _load_script_module(
    "audit_dialogs_inventory",
    _SCRIPTS_DIR / "audit_dialogs_inventory.py",
)


class TestAuditBaselineMetricsCLI:
    """CLI contract tests for scripts/audit_baseline_metrics.py."""

    @pytest.mark.timeout(30)
    def test_default_prints_markdown_to_stdout(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = _baseline_metrics.main([])
        captured = capsys.readouterr()
        assert code == 0
        assert "# SOLID Audit Baseline Metrics" in captured.out
        assert "## MainWindow regression guard" in captured.out
        assert captured.err == ""

    @pytest.mark.timeout(30)
    def test_json_export_writes_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        output_file = tmp_path / "baseline_metrics.json"
        code = _baseline_metrics.main(["--json", str(output_file)])
        captured = capsys.readouterr()
        assert code == 0
        assert captured.out == ""
        assert captured.err == ""
        assert output_file.is_file()

        data: list[dict[str, Any]] = json.loads(output_file.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) > 0
        assert "path" in data[0]
        assert "total_lines" in data[0]

    @pytest.mark.timeout(30)
    def test_markdown_export_creates_parent_and_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        output_file = tmp_path / "nested" / "reports" / "baseline_metrics.md"
        code = _baseline_metrics.main(["--markdown", str(output_file)])
        captured = capsys.readouterr()
        assert code == 0
        assert captured.out == ""
        assert captured.err == ""
        assert output_file.is_file()

        content = output_file.read_text(encoding="utf-8")
        assert "# SOLID Audit Baseline Metrics" in content
        assert "## MainWindow regression guard" in content

    @pytest.mark.timeout(30)
    def test_combined_json_and_markdown(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        json_file = tmp_path / "combined.json"
        md_file = tmp_path / "combined.md"
        code = _baseline_metrics.main(
            ["--json", str(json_file), "--markdown", str(md_file)]
        )
        captured = capsys.readouterr()
        assert code == 0
        assert captured.out == ""
        assert captured.err == ""
        assert json_file.is_file()
        assert md_file.is_file()

    @pytest.mark.timeout(30)
    def test_check_clean_returns_zero(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = _baseline_metrics.main(["--check"])
        captured = capsys.readouterr()
        assert code == 0
        assert captured.err == ""

    @pytest.mark.timeout(30)
    def test_check_violation_returns_one_and_writes_stderr(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        synthetic_violations = [
            "pypost/ui/main_window.py: 9999 lines exceeds cap 477",
            "pypost/core/storage.py: 1234 lines exceeds cap 380",
        ]
        monkeypatch.setattr(
            _baseline_metrics,
            "check_caps",
            lambda: list(synthetic_violations),
        )
        code = _baseline_metrics.main(["--check"])
        captured = capsys.readouterr()
        assert code == 1
        for violation in synthetic_violations:
            assert violation in captured.err

    @pytest.mark.timeout(30)
    def test_invalid_argument_exits_code_two(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            _baseline_metrics.main(["--nonexistent-flag"])
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "unrecognized arguments: --nonexistent-flag" in captured.err

    @pytest.mark.timeout(30)
    def test_missing_option_argument_exits_code_two(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            _baseline_metrics.main(["--json"])
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "expected one argument" in captured.err


class TestAuditDialogsInventoryCLI:
    """CLI contract tests for scripts/audit_dialogs_inventory.py."""

    @pytest.mark.timeout(30)
    def test_default_prints_tsv_to_stdout(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = _dialogs_inventory.main([])
        captured = capsys.readouterr()
        assert code == 0
        assert captured.err == ""
        assert "TOTAL\t" in captured.out
        assert "pypost/ui/dialogs/" in captured.out

    @pytest.mark.timeout(30)
    def test_markdown_flag_prints_table(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = _dialogs_inventory.main(["--markdown"])
        captured = capsys.readouterr()
        assert code == 0
        assert captured.err == ""
        assert "| Module | LOC | Non-empty |" in captured.out
        assert "| **Total** |" in captured.out

    @pytest.mark.timeout(30)
    def test_json_flag_prints_valid_json(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = _dialogs_inventory.main(["--json"])
        captured = capsys.readouterr()
        assert code == 0
        assert captured.err == ""
        data: dict[str, Any] = json.loads(captured.out)
        assert "modules" in data
        assert isinstance(data["modules"], list)
        assert len(data["modules"]) > 0
        assert "total_lines" in data
        assert "audit_era_grouped_loc" in data

    @pytest.mark.timeout(30)
    def test_check_clean_returns_zero_and_reports_ok(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = _dialogs_inventory.main(["--check"])
        captured = capsys.readouterr()
        assert code == 0
        assert captured.err == ""
        assert "covered by audit report" in captured.out

    @pytest.mark.timeout(30)
    def test_check_missing_report_returns_one(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        missing_report = _dialogs_inventory.REPO_ROOT / "nonexistent-audit-report.md"
        monkeypatch.setattr(_dialogs_inventory, "AUDIT_REPORT", missing_report)
        code = _dialogs_inventory.main(["--check"])
        captured = capsys.readouterr()
        assert code == 1
        assert "Missing audit report: nonexistent-audit-report.md" in captured.err

    @pytest.mark.timeout(30)
    def test_check_missing_dialog_returns_one(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        synthetic_issues = [
            "Audit report missing dialog module(s): fake_dialog.py, missing_dialog.py"
        ]
        monkeypatch.setattr(
            _dialogs_inventory,
            "check_audit_report_covers",
            lambda modules: list(synthetic_issues),
        )
        code = _dialogs_inventory.main(["--check"])
        captured = capsys.readouterr()
        assert code == 1
        assert synthetic_issues[0] in captured.err

    @pytest.mark.timeout(30)
    def test_invalid_argument_exits_code_two(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            _dialogs_inventory.main(["--invalid-argument"])
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "unrecognized arguments: --invalid-argument" in captured.err

    @pytest.mark.timeout(30)
    def test_unexpected_positional_arg_exits_code_two(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            _dialogs_inventory.main(["--json", "extra_arg"])
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "unrecognized arguments: extra_arg" in captured.err
