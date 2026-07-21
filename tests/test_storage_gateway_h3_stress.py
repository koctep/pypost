"""H3 stress: rapid gateway load/save + pending restart under GC churn.

Investigation harness for PYPOST-829. Looks for stranded load/save completion
outcomes after worker finish (busy=False / pending=False / worker_running=False
while expected signals never arrive). Architecture default: >=200 cycles per
gateway including pending-restart paths, with gc.collect between batches.
"""

from __future__ import annotations

import gc
import unittest
from unittest.mock import MagicMock

import pytest
from PySide6.QtTest import QSignalSpy

from pypost.core.qt.collection_storage_gateway import CollectionStorageGateway
from pypost.core.qt.environment_storage_gateway import EnvironmentStorageGateway
from pypost.models.models import Collection, Environment
from tests.helpers.process_until import gateway_timeout_detail, process_until

pytestmark = pytest.mark.timeout(120)

# Architecture default: >=200 rapid cycles per gateway (PYPOST-829).
_CYCLE_COUNT = 200
_BATCH_SIZE = 25
_WAIT_MS = 5_000


def _make_env(name: str) -> Environment:
    return Environment(name=name, variables={"A": "1"})


def _assert_idle_not_stranded(gateway, spy_count: int, expected: int) -> None:
    """Fail with H3 fingerprint if idle but completion never arrived."""
    if spy_count >= expected:
        return
    detail = gateway_timeout_detail(gateway)()
    raise AssertionError(
        f"H3 fingerprint: expected {expected} completions, got {spy_count}; {detail}"
    )


@pytest.mark.usefixtures("qapp")
class TestStorageGatewayH3Stress(unittest.TestCase):
    def test_env_gateway_rapid_load_save_and_pending_restart(self):
        """>=200 env cycles: load, save, save-then-queued-load; GC between batches."""
        storage = MagicMock()
        storage.load_environments.return_value = [_make_env("Loaded")]
        gateway = EnvironmentStorageGateway(storage)
        load_spy = QSignalSpy(gateway.load_completed)
        save_spy = QSignalSpy(gateway.save_completed)
        fail_load = QSignalSpy(gateway.load_failed)
        fail_save = QSignalSpy(gateway.save_failed)

        expected_loads = 0
        expected_saves = 0

        for i in range(_CYCLE_COUNT):
            # Plain load
            gateway.load_async()
            expected_loads += 1
            process_until(
                lambda el=expected_loads: load_spy.count() >= el
                or fail_load.count() >= 1,
                timeout_ms=_WAIT_MS,
                timeout_detail=gateway_timeout_detail(gateway),
            )
            self.assertEqual(fail_load.count(), 0, "unexpected load_failed")
            _assert_idle_not_stranded(gateway, load_spy.count(), expected_loads)

            # Plain save
            gateway.save_async([_make_env(f"Save-{i}")])
            expected_saves += 1
            process_until(
                lambda es=expected_saves: save_spy.count() >= es
                or fail_save.count() >= 1,
                timeout_ms=_WAIT_MS,
                timeout_detail=gateway_timeout_detail(gateway),
            )
            self.assertEqual(fail_save.count(), 0, "unexpected save_failed")
            _assert_idle_not_stranded(gateway, save_spy.count(), expected_saves)

            # Save then queued load (pending restart path)
            gateway.save_async([_make_env(f"Pend-{i}")])
            gateway.load_async()
            expected_saves += 1
            expected_loads += 1
            process_until(
                lambda es=expected_saves, el=expected_loads: (
                    save_spy.count() >= es and load_spy.count() >= el
                )
                or fail_save.count() >= 1
                or fail_load.count() >= 1,
                timeout_ms=_WAIT_MS,
                timeout_detail=gateway_timeout_detail(gateway),
            )
            self.assertEqual(fail_load.count(), 0)
            self.assertEqual(fail_save.count(), 0)
            _assert_idle_not_stranded(gateway, load_spy.count(), expected_loads)
            _assert_idle_not_stranded(gateway, save_spy.count(), expected_saves)

            if (i + 1) % _BATCH_SIZE == 0:
                self.assertFalse(gateway.has_pending_work())
                self.assertFalse(gateway.is_busy())
                gc.collect()

        self.assertEqual(load_spy.count(), expected_loads)
        self.assertEqual(save_spy.count(), expected_saves)
        self.assertFalse(gateway.has_pending_work())

    def test_collection_gateway_rapid_load_and_queued_restart(self):
        """>=200 collection cycles: load + queued-second-load; GC between batches."""
        storage = MagicMock()
        storage.load_collections.return_value = [
            Collection(name="Loaded", requests=[]),
        ]
        gateway = CollectionStorageGateway(storage)
        spy = QSignalSpy(gateway.load_completed)
        fail_spy = QSignalSpy(gateway.load_failed)

        expected = 0
        for i in range(_CYCLE_COUNT):
            # Plain load
            gateway.load_async()
            expected += 1
            process_until(
                lambda e=expected: spy.count() >= e or fail_spy.count() >= 1,
                timeout_ms=_WAIT_MS,
                timeout_detail=gateway_timeout_detail(gateway),
            )
            self.assertEqual(fail_spy.count(), 0)
            _assert_idle_not_stranded(gateway, spy.count(), expected)

            # Queued second load (pending restart)
            gateway.load_async()
            gateway.load_async()
            expected += 2
            process_until(
                lambda e=expected: spy.count() >= e or fail_spy.count() >= 1,
                timeout_ms=_WAIT_MS,
                timeout_detail=gateway_timeout_detail(gateway),
            )
            self.assertEqual(fail_spy.count(), 0)
            _assert_idle_not_stranded(gateway, spy.count(), expected)

            if (i + 1) % _BATCH_SIZE == 0:
                self.assertFalse(gateway.has_pending_work())
                self.assertFalse(gateway.is_busy())
                gc.collect()

        self.assertEqual(spy.count(), expected)
        self.assertFalse(gateway.has_pending_work())
