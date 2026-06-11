"""Regression guards for PYPOST-374 dialog SOLID audit inventory."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(30)

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_spec = importlib.util.spec_from_file_location(
    "audit_dialogs_inventory",
    _SCRIPTS / "audit_dialogs_inventory.py",
)
assert _spec and _spec.loader
_inventory = importlib.util.module_from_spec(_spec)
sys.modules["audit_dialogs_inventory"] = _inventory
_spec.loader.exec_module(_inventory)


class TestDialogsAuditInventory(unittest.TestCase):
    def test_discover_matches_dialogs_directory(self):
        modules = _inventory.discover_dialog_modules()
        on_disk = sorted(
            path.name
            for path in (_inventory.DIALOGS_DIR).glob("*.py")
            if path.name != "__init__.py"
        )
        discovered = [module.filename for module in modules]
        self.assertEqual(discovered, on_disk)

    def test_audit_report_lists_every_dialog_module(self):
        issues = _inventory.check_audit_report_covers(_inventory.discover_dialog_modules())
        self.assertEqual(issues, [], msg="\n".join(issues))

    def test_total_loc_above_audit_era_grouped_estimate(self):
        modules = _inventory.discover_dialog_modules()
        total = _inventory.total_loc(modules)
        self.assertGreater(
            total,
            _inventory.AUDIT_ERA_GROUPED_LOC,
            msg=(
                "Total dialog LOC should exceed PYPOST-40 grouped ~400 LOC "
                "(scope grew with MCP dialogs and Settings)"
            ),
        )
