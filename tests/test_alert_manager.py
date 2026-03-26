"""Unit tests for AlertManager and AlertPayload."""
import gc
import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pypost.core.alert_manager import AlertManager, AlertPayload


def _make_payload(**kwargs) -> AlertPayload:
    defaults = dict(
        request_name="test-req",
        endpoint="http://example.com/api",
        retries_attempted=3,
        final_error_category="network",
        final_error_message="Connection refused",
    )
    defaults.update(kwargs)
    return AlertPayload(**defaults)


class TestAlertPayload(unittest.TestCase):
    def test_to_dict_contains_all_fields(self):
        p = _make_payload()
        d = p.to_dict()
        self.assertIn("timestamp", d)
        self.assertEqual(d["request_name"], "test-req")
        self.assertEqual(d["endpoint"], "http://example.com/api")
        self.assertEqual(d["retries_attempted"], 3)
        self.assertEqual(d["final_error_category"], "network")
        self.assertEqual(d["final_error_message"], "Connection refused")

    def test_timestamp_is_iso8601_utc(self):
        p = _make_payload()
        # Should end with +00:00 or contain a time separator
        self.assertIn("T", p.timestamp)

    def test_to_dict_is_json_serialisable(self):
        p = _make_payload()
        serialised = json.dumps(p.to_dict())
        parsed = json.loads(serialised)
        self.assertEqual(parsed["request_name"], "test-req")


class TestAlertManagerLogFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = Path(self.tmpdir) / "alerts.log"

    def _make_manager(self, **kwargs) -> AlertManager:
        return AlertManager(log_path=self.log_path, **kwargs)

    def test_emit_writes_json_to_log_file(self):
        mgr = self._make_manager()
        p = _make_payload()
        mgr.emit(p)
        content = self.log_path.read_text(encoding="utf-8")
        self.assertTrue(content.strip())
        data = json.loads(content.strip())
        self.assertEqual(data["endpoint"], p.endpoint)

    def test_emit_multiple_entries(self):
        mgr = self._make_manager()
        for i in range(3):
            mgr.emit(_make_payload(retries_attempted=i))
        lines = [l for l in self.log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(len(lines), 3)

    def test_log_file_created_automatically(self):
        nested = Path(self.tmpdir) / "sub" / "dir" / "alerts.log"
        mgr = AlertManager(log_path=nested)
        mgr.emit(_make_payload())
        self.assertTrue(nested.exists())

    def test_logger_does_not_propagate(self):
        mgr = self._make_manager()
        self.assertFalse(mgr._logger.propagate)

    def test_logger_level_is_info(self):
        mgr = self._make_manager()
        self.assertEqual(mgr._logger.level, logging.INFO)


class TestAlertManagerWebhook(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = Path(self.tmpdir) / "alerts.log"

    def test_webhook_called_when_url_set(self):
        mgr = AlertManager(
            log_path=self.log_path,
            webhook_url="http://hooks.example.com/alert",
        )
        with patch("pypost.core.alert_manager.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            mgr.emit(_make_payload())
        mock_post.assert_called_once()

    def test_webhook_not_called_when_url_not_set(self):
        mgr = AlertManager(log_path=self.log_path)
        with patch("pypost.core.alert_manager.requests.post") as mock_post:
            mgr.emit(_make_payload())
        mock_post.assert_not_called()

    def test_webhook_includes_auth_header_when_set(self):
        mgr = AlertManager(
            log_path=self.log_path,
            webhook_url="http://hooks.example.com/alert",
            webhook_auth_header="Bearer secret-token",
        )
        with patch("pypost.core.alert_manager.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            mgr.emit(_make_payload())
        _, kwargs = mock_post.call_args
        self.assertIn("Authorization", kwargs["headers"])
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer secret-token")

    def test_webhook_failure_does_not_propagate(self):
        mgr = AlertManager(
            log_path=self.log_path,
            webhook_url="http://hooks.example.com/alert",
        )
        with patch(
            "pypost.core.alert_manager.requests.post",
            side_effect=ConnectionError("unreachable"),
        ):
            # Must NOT raise
            mgr.emit(_make_payload())

    def test_webhook_timeout_does_not_propagate(self):
        import requests as req_lib
        mgr = AlertManager(
            log_path=self.log_path,
            webhook_url="http://hooks.example.com/alert",
        )
        with patch(
            "pypost.core.alert_manager.requests.post",
            side_effect=req_lib.Timeout("timed out"),
        ):
            mgr.emit(_make_payload())

    def test_webhook_sends_json_body(self):
        mgr = AlertManager(
            log_path=self.log_path,
            webhook_url="http://hooks.example.com/alert",
        )
        p = _make_payload()
        with patch("pypost.core.alert_manager.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            mgr.emit(p)
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"], p.to_dict())

    def test_webhook_timeout_is_five_seconds(self):
        mgr = AlertManager(
            log_path=self.log_path,
            webhook_url="http://hooks.example.com/alert",
        )
        with patch("pypost.core.alert_manager.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            mgr.emit(_make_payload())
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["timeout"], 5.0)


class TestAlertManagerAccumulation(unittest.TestCase):
    """Regression tests for handler accumulation via id() reuse and missing close()."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log_path = Path(self.tmpdir) / "alerts.log"

    def _line_count(self) -> int:
        if not self.log_path.exists():
            return 0
        return len([l for l in self.log_path.read_text(encoding="utf-8").splitlines() if l.strip()])

    def test_no_accumulation_via_close(self):
        """Each closed manager writes exactly one line; N+1 managers write N+1 lines."""
        N = 5
        for _ in range(N):
            mgr = AlertManager(log_path=self.log_path)
            mgr.emit(_make_payload())
            mgr.close()
        mgr = AlertManager(log_path=self.log_path)
        mgr.emit(_make_payload())
        mgr.close()
        self.assertEqual(self._line_count(), N + 1)

    def test_no_accumulation_via_gc_id_reuse(self):
        """Handler guard evicts stale handlers when CPython reuses a memory address."""
        N = 5
        for _ in range(N):
            mgr = AlertManager(log_path=self.log_path)
            mgr.emit(_make_payload())
            del mgr
            gc.collect()
        mgr = AlertManager(log_path=self.log_path)
        mgr.emit(_make_payload())
        mgr.close()
        self.assertEqual(self._line_count(), N + 1)


if __name__ == "__main__":
    unittest.main()
