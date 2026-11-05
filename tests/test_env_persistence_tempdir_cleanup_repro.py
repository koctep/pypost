"""PYPOST-1311 durable repro: temp-dir cleanup vs in-flight encrypted async load.

Desired behavior (asserted here): after the missing-key product checks, leaving the
temporary workspace must not raise ``OSError`` / ``Directory not empty``.

Forces a gated encrypted async load that keeps writing under the workspace while
the worker is in flight. The Step 4 fence (``release_load`` +
``wait_storage_idle`` + ``teardown``) must run before ``TemporaryDirectory``
cleanup so ``rmtree`` succeeds.
"""

from __future__ import annotations

import itertools
import shutil
import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pypost.models.models import Environment
from pypost.models.settings import AppSettings
from pypost.ui.presenters.env_presenter import EnvPresenter

pytestmark = pytest.mark.timeout(60)


class _GatedWorkspaceStorage:
    """Storage double: holds async load and keeps writing under ``workspace``."""

    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace
        self.load_started = threading.Event()
        self.release_load = threading.Event()
        self._n = itertools.count()

    def load_environments(self) -> list[Environment]:
        self.load_started.set()
        # Recreate unique subtrees while gated so TemporaryDirectory.cleanup
        # races the still-running worker (errno 39 Directory not empty).
        while not self.release_load.is_set():
            index = next(self._n)
            try:
                hold = self._workspace / f"hold-{index}"
                hold.mkdir(exist_ok=True)
                (hold / "chunk").write_text("in-flight", encoding="utf-8")
                nested = hold / "nested"
                nested.mkdir(exist_ok=True)
                (nested / "chunk").write_text("in-flight", encoding="utf-8")
            except OSError:
                pass
        return []

    def save_environments(self, environments: list[Environment]) -> None:
        return None

    def serialize_environment_records(
        self,
        environments: list[Environment],
        *,
        target_envelope_version: int | None = None,
    ) -> list[dict]:
        return [environment.model_dump(mode="json") for environment in environments]


def _make_encrypted_presenter(storage: _GatedWorkspaceStorage) -> EnvPresenter:
    return EnvPresenter(
        storage,
        MagicMock(),
        MagicMock(),
        AppSettings(env_encryption_enabled=True),
        lambda: [],
        MagicMock(),
    )


def test_tempdir_cleanup_survives_in_flight_encrypted_async_load(qapp):  # noqa: ARG001
    """Temp workspace cleanup must succeed after encrypted async missing-key load.

    Forces an in-flight ``EnvironmentStorageGateway`` load (encryption on) against
    a temp workspace, then applies the release + idle + teardown fence before
    ``TemporaryDirectory`` cleanup (same contract as the named e2e).
    """
    tmp = tempfile.TemporaryDirectory()
    workspace = Path(tmp.name)
    storage = _GatedWorkspaceStorage(workspace)
    presenter = _make_encrypted_presenter(storage)
    try:
        presenter.load_environments()
        assert storage.load_started.wait(timeout=5), "encrypted async load did not start"

        # Same product meaning as the named e2e (no environment shown yet).
        assert presenter.environment_count() == 1
        assert presenter.current_environment_index() == 0

        # Fence: release gate, settle worker, teardown — then exit temp dir.
        storage.release_load.set()
        assert presenter.wait_storage_idle(timeout_ms=5_000)
        presenter.teardown(timeout_ms=5_000)
        tmp.cleanup()
    finally:
        storage.release_load.set()
        presenter.wait_storage_idle(timeout_ms=5_000)
        presenter.teardown(timeout_ms=5_000)
        shutil.rmtree(workspace, ignore_errors=True)
