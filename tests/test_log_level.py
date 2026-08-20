"""Tests for configurable application log level (PYPOST-743)."""
import logging
import unittest

import pytest

from pypost.main import _resolve_log_level
from pypost.models.settings import AppSettings

pytestmark = pytest.mark.timeout(30)


class TestResolveLogLevel(unittest.TestCase):
    def test_debug_level(self):
        self.assertEqual(_resolve_log_level("DEBUG"), logging.DEBUG)

    def test_info_default_for_unknown(self):
        self.assertEqual(_resolve_log_level("VERBOSE"), logging.INFO)

    def test_settings_default_is_info(self):
        self.assertEqual(AppSettings().log_level, "INFO")


if __name__ == "__main__":
    unittest.main()
