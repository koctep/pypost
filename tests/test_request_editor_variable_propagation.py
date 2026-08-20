"""RequestWidget variable snapshot fan-out (PYPOST-128)."""

import pytest

import unittest

from pypost.ui.widgets.request_editor import RequestWidget

pytestmark = pytest.mark.timeout(60)


@pytest.mark.usefixtures("qapp")

class TestRequestWidgetVariablePropagation(unittest.TestCase):
    def setUp(self):
        self.widget = RequestWidget()

    def test_set_variables_reaches_all_snapshot_targets(self):
        variables = {"HOST": "example.com", "TOKEN": "secret"}
        self.widget.set_variables(variables)
        for target in self.widget._variable_snapshot_targets:
            self.assertEqual(target._variables, variables)

    def test_set_hidden_keys_reaches_all_snapshot_targets(self):
        hidden = {"TOKEN", "API_KEY"}
        self.widget.set_hidden_keys(hidden)
        for target in self.widget._variable_snapshot_targets:
            self.assertEqual(target._hidden_keys, hidden)
