import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from pypost.core.history_manager import HistoryManager
from pypost.models.models import HistoryEntry


def _make_entry(**kwargs) -> HistoryEntry:
    defaults = dict(
        timestamp="2026-03-17T14:30:00.000000Z",
        method="GET",
        url="https://example.com/api",
        headers={},
        body="",
        status_code=200,
        response_time_ms=42.0,
    )
    defaults.update(kwargs)
    return HistoryEntry(**defaults)


class TestHistoryManagerLoad(unittest.TestCase):
    def test_load_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            hm = _manager_at(td)
            self.assertEqual([], hm.get_entries())

    def test_load_corrupt_file(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "history.json"
            p.write_text("not valid json", encoding="utf-8")
            hm = _manager_at(td, path=p)
            self.assertEqual([], hm.get_entries())


class TestHistoryManagerAppend(unittest.TestCase):
    def test_append_single_entry(self):
        with tempfile.TemporaryDirectory() as td:
            hm = _manager_at(td)
            hm.append(_make_entry(url="https://a.com"))
            entries = hm.get_entries()
            self.assertEqual(1, len(entries))
            self.assertEqual("https://a.com", entries[0].url)
            hm.flush()

    def test_append_enforces_cap(self):
        with tempfile.TemporaryDirectory() as td:
            hm = _manager_at(td, max_entries=500)
            for i in range(501):
                hm.append(_make_entry(url=f"https://example.com/{i}"))
            entries = hm.get_entries()
            self.assertEqual(500, len(entries))
            # Most recent is first
            self.assertEqual("https://example.com/500", entries[0].url)
            hm.flush()

    def test_get_entries_newest_first(self):
        with tempfile.TemporaryDirectory() as td:
            hm = _manager_at(td)
            hm.append(_make_entry(url="https://first.com", timestamp="2026-01-01T00:00:00Z"))
            hm.append(_make_entry(url="https://second.com", timestamp="2026-01-02T00:00:00Z"))
            hm.append(_make_entry(url="https://third.com", timestamp="2026-01-03T00:00:00Z"))
            entries = hm.get_entries()
            # Entries are prepended, so last appended = first in list
            self.assertEqual("https://third.com", entries[0].url)
            self.assertEqual("https://second.com", entries[1].url)
            self.assertEqual("https://first.com", entries[2].url)
            hm.flush()


class TestHistoryManagerDelete(unittest.TestCase):
    def test_delete_entry(self):
        with tempfile.TemporaryDirectory() as td:
            hm = _manager_at(td)
            e1 = _make_entry(url="https://a.com")
            e2 = _make_entry(url="https://b.com")
            hm.append(e1)
            hm.append(e2)
            hm.delete_entry(e1.id)
            entries = hm.get_entries()
            self.assertEqual(1, len(entries))
            self.assertEqual(e2.id, entries[0].id)
            hm.flush()


class TestHistoryManagerClear(unittest.TestCase):
    def test_clear(self):
        with tempfile.TemporaryDirectory() as td:
            hm = _manager_at(td)
            hm.append(_make_entry())
            hm.append(_make_entry())
            hm.clear()
            self.assertEqual([], hm.get_entries())
            hm.flush()


class TestHistoryManagerPersistence(unittest.TestCase):
    def test_save_and_reload(self):
        with tempfile.TemporaryDirectory() as td:
            hm1 = _manager_at(td)
            entry = _make_entry(url="https://persist.com", status_code=201)
            hm1.append(entry)
            hm1.flush()

            hm2 = _manager_at(td)
            entries = hm2.get_entries()
            self.assertEqual(1, len(entries))
            self.assertEqual("https://persist.com", entries[0].url)
            self.assertEqual(201, entries[0].status_code)


class TestHistoryManagerConcurrency(unittest.TestCase):
    def test_concurrent_appends(self):
        with tempfile.TemporaryDirectory() as td:
            hm = _manager_at(td, max_entries=500)
            threads = []
            for i in range(50):
                t = threading.Thread(
                    target=hm.append,
                    args=(_make_entry(url=f"https://example.com/{i}"),),
                )
                threads.append(t)
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            hm.flush()
            entries = hm.get_entries()
            self.assertEqual(50, len(entries))
            urls = {e.url for e in entries}
            self.assertEqual(50, len(urls))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _manager_at(tmp_dir: str, max_entries: int = 500, path: Path | None = None) -> HistoryManager:
    """Create a HistoryManager that stores its file under tmp_dir."""
    file_path = path if path is not None else Path(tmp_dir) / "history.json"
    return HistoryManager(max_entries=max_entries, history_path=file_path)


if __name__ == "__main__":
    unittest.main()


class TestHistoryManagerDurability(unittest.TestCase):
    """History replaces its file atomically, as the other stores do."""

    def test_failed_replace_keeps_the_previous_history(self):
        with tempfile.TemporaryDirectory() as td:
            hm = _manager_at(td)
            hm.append(_make_entry(url="https://example.com/first"))
            hm.flush()
            before = Path(td, "history.json").read_text(encoding="utf-8")

            with patch(
                "pypost.core.history_manager.os.replace",
                side_effect=OSError("replace failed"),
            ):
                hm.append(_make_entry(url="https://example.com/second"))
                hm.flush()

            self.assertEqual(
                before, Path(td, "history.json").read_text(encoding="utf-8")
            )

    def test_failed_replace_leaves_no_temporary_file(self):
        with tempfile.TemporaryDirectory() as td:
            hm = _manager_at(td)

            with patch(
                "pypost.core.history_manager.os.replace",
                side_effect=OSError("replace failed"),
            ):
                hm.append(_make_entry())
                hm.flush()

            self.assertFalse(Path(td, "history.json.tmp").exists())

    def test_flush_waits_for_a_save_started_on_another_thread(self):
        """Behavioural cover for flush(), not a probe of the publication race.

        The race it guards against -- flush() reading _save_thread before
        _save_async has published it -- has too narrow a window to provoke
        reliably, so this asserts the contract rather than the timing.
        """
        with tempfile.TemporaryDirectory() as td:
            hm = _manager_at(td)

            def append_from_another_thread():
                hm.append(_make_entry(url="https://example.com/other"))

            worker = threading.Thread(target=append_from_another_thread)
            worker.start()
            worker.join()
            hm.flush()

            saved = json.loads(Path(td, "history.json").read_text(encoding="utf-8"))
            self.assertEqual(
                ["https://example.com/other"], [e["url"] for e in saved]
            )

