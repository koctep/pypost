"""Unit tests for EnvVariableSnapshot (PYPOST-577)."""

import pytest

import unittest

from pypost.core.env_variable_snapshot import EnvVariableSnapshot

pytestmark = pytest.mark.timeout(30)


class TestEnvVariableSnapshot(unittest.TestCase):
    def test_snapshot_variables_returns_copy(self):
        snap = EnvVariableSnapshot()
        snap.update({"A": "1"})
        first = snap.snapshot_variables()
        first["A"] = "mutated"
        self.assertEqual(snap.snapshot_variables(), {"A": "1"})

    def test_update_replaces_variables_and_hidden_keys(self):
        snap = EnvVariableSnapshot()
        snap.update({"X": "1"}, {"X"})
        snap.update({"Y": "2"}, set())
        self.assertEqual(snap.snapshot_variables(), {"Y": "2"})
        self.assertEqual(snap.snapshot_hidden_keys(), set())

    def test_snapshot_hidden_keys_returns_copy(self):
        snap = EnvVariableSnapshot()
        snap.update({}, {"SECRET"})
        keys = snap.snapshot_hidden_keys()
        keys.add("OTHER")
        self.assertEqual(snap.snapshot_hidden_keys(), {"SECRET"})


if __name__ == "__main__":
    unittest.main()
