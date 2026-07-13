"""Tests for settings webhook auth encryption at rest (PYPOST-708)."""

import json
import tempfile
import unittest
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

from pypost.core.config_manager import ConfigManager
from pypost.models.settings import AppSettings

pytestmark = pytest.mark.timeout(30)


class TestSettingsWebhookAuthEncryption(unittest.TestCase):
    def test_save_encrypts_webhook_auth_on_disk(self):
        key = Fernet.generate_key().decode("utf-8")
        with tempfile.TemporaryDirectory() as td:
            with patch.dict("os.environ", {"PYPOST_ENV_ENCRYPTION_KEY": key}, clear=False):
                with patch("pypost.core.config_manager.user_config_dir", return_value=td):
                    cm = ConfigManager()
                    settings = AppSettings(alert_webhook_auth_header="Bearer secret-token")
                    cm.save_config(settings)
                    on_disk = json.loads(cm.config_path.read_text(encoding="utf-8"))
                    self.assertNotIn("alert_webhook_auth_header", on_disk)
                    self.assertIn("alert_webhook_auth_header_encrypted", on_disk)
                    reloaded = cm.load_config()
                    self.assertEqual(
                        reloaded.alert_webhook_auth_header, "Bearer secret-token"
                    )

    def test_legacy_plaintext_webhook_auth_still_loads(self):
        with tempfile.TemporaryDirectory() as td:
            with patch("pypost.core.config_manager.user_config_dir", return_value=td):
                cm = ConfigManager()
                cm.config_path.write_text(
                    json.dumps(
                        {
                            "alert_webhook_auth_header": "Bearer legacy",
                            "revision": 0,
                        }
                    ),
                    encoding="utf-8",
                )
                reloaded = cm.load_config()
                self.assertEqual(reloaded.alert_webhook_auth_header, "Bearer legacy")
