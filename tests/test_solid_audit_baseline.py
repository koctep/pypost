"""Regression guards for PYPOST-40 / PYPOST-376 SOLID audit baseline metrics."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(30)

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_spec = importlib.util.spec_from_file_location(
    "audit_baseline_metrics",
    _SCRIPTS / "audit_baseline_metrics.py",
)
assert _spec and _spec.loader
_baseline = importlib.util.module_from_spec(_spec)
sys.modules["audit_baseline_metrics"] = _baseline
_spec.loader.exec_module(_baseline)


class TestSolidAuditBaseline(unittest.TestCase):
    def test_main_window_file_loc_within_cap(self):
        metrics = _baseline.measure_file("pypost/ui/main_window.py")
        self.assertLessEqual(
            metrics.total_lines,
            metrics.cap,
            msg=f"main_window.py grew to {metrics.total_lines} (cap {metrics.cap})",
        )

    def test_main_window_class_loc_within_cap(self):
        metrics = _baseline.measure_file("pypost/ui/main_window.py")
        class_loc = metrics.class_lines[_baseline.MAIN_WINDOW_CLASS]
        self.assertLessEqual(
            class_loc,
            _baseline.MAIN_WINDOW_CLASS_CAP,
            msg=(
                f"{_baseline.MAIN_WINDOW_CLASS} class is {class_loc} lines "
                f"(cap {_baseline.MAIN_WINDOW_CLASS_CAP})"
            ),
        )

    def test_audit_module_inventory_within_caps(self):
        violations = _baseline.check_caps()
        self.assertEqual(
            violations,
            [],
            msg="Baseline cap violations:\n" + "\n".join(violations),
        )
