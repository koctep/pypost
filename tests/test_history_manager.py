import json
import threading
import time
import unittest
from pathlib import Path

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
    def test_load_missing_file(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            hm = _manager_at(td)
            self.assertEqual([], hm.get_entries())

    def test_load_corrupt_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "history.json"
            p.write_text("not valid json", encoding="utf-8")
            hm = _manager_at(td, path=p)
            self.assertEqual([], hm.get_entries())


class TestHistoryManagerAppend(unittest.TestCase):
    def test_append_single_entry(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            hm = _manager_at(td)
            hm.append(_make_entry(url="https://a.com"))
            entries = hm.get_entries()
            self.assertEqual(1, len(entries))
            self.assertEqual("https://a.com", entries[0].url)
            hm.flush()

    def test_append_enforces_cap(self):
        import tempfile
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
        import tempfile
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
        import tempfile
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
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            hm = _manager_at(td)
            hm.append(_make_entry())
            hm.append(_make_entry())
            hm.clear()
            self.assertEqual([], hm.get_entries())
            hm.flush()


class TestHistoryManagerPersistence(unittest.TestCase):
    def test_save_and_reload(self):
        import tempfile
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
        import tempfile
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
    hm = HistoryManager.__new__(HistoryManager)
    hm._max_entries = max_entries
    hm._lock = threading.Lock()
    hm._save_lock = threading.Lock()
    hm._save_running = False
    hm._save_pending = False
    hm._save_thread = None
    hm._entries = []
    if path is not None:
        hm._history_path = path
    else:
        hm._history_path = Path(tmp_dir) / "history.json"
    hm._load()
    return hm


if __name__ == "__main__":
    unittest.main()
