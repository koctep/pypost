"""Unit tests for HiddenToggleLogPolicy (PYPOST-448)."""

import unittest

from pypost.core.hidden_toggle_log_policy import HiddenToggleLogPolicy
from pypost.core.constants import HIDDEN_MASK


class TestHiddenToggleLogPolicy(unittest.TestCase):
    def test_format_key_name_enabled_returns_key(self):
        result = HiddenToggleLogPolicy.format_key_name(
            "API_KEY",
            log_hidden_key_names=True,
        )
        self.assertEqual(result, "API_KEY")

    def test_format_key_name_disabled_returns_hidden_mask(self):
        result = HiddenToggleLogPolicy.format_key_name(
            "API_KEY",
            log_hidden_key_names=False,
        )
        self.assertEqual(result, HIDDEN_MASK)


if __name__ == "__main__":
    unittest.main()
