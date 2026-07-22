"""PYPOST-857: seeded workspace present after agent session ready."""

from __future__ import annotations

import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QApplication, QComboBox, QTreeView

from pypost.agent import AgentAppSession
from pypost.core.storage import StorageManager
from pypost.fixtures.agent_e2e_seed import (
    SEED_COLLECTION_NAME,
    SEED_ENV_NAME,
    SEED_GET_REQUEST_NAME,
    SEED_POST_REQUEST_NAME,
    build_agent_e2e_seed_collection,
    build_agent_e2e_seed_environments,
    write_agent_e2e_seed,
)
from pypost.ui.widget_ids import COLLECTION_TREE, ENV_SELECTOR
from tests.helpers.agent_e2e_seed import seeded_agent_dirs

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]


def _tree_texts(tree: QTreeView) -> tuple[list[str], list[str]]:
    model = tree.model()
    assert isinstance(model, QStandardItemModel)
    collections: list[str] = []
    requests: list[str] = []
    for row in range(model.rowCount()):
        col_item = model.item(row)
        collections.append(col_item.text())
        for child_row in range(col_item.rowCount()):
            requests.append(col_item.child(child_row).text())
    return collections, requests


def _env_item_texts(selector: QComboBox) -> list[str]:
    return [selector.itemText(i) for i in range(selector.count())]


def test_write_agent_e2e_seed_persists_inventory(tmp_path: Path) -> None:
    """Builders + StorageManager writer persist the documented inventory."""
    write_agent_e2e_seed(tmp_path)
    storage = StorageManager(data_dir=tmp_path)
    assert storage.load_collections() == [build_agent_e2e_seed_collection()]
    assert storage.load_environments() == build_agent_e2e_seed_environments()


def test_write_agent_e2e_seed_logs_failure_and_reraises(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """PYPOST-862: persist failure logs agent_e2e_seed_failed and re-raises."""
    storage = MagicMock()
    storage.save_collection.side_effect = OSError("disk full")
    with patch(
        "pypost.fixtures.agent_e2e_seed.StorageManager",
        return_value=storage,
    ):
        with caplog.at_level(
            logging.ERROR,
            logger="pypost.fixtures.agent_e2e_seed",
        ):
            with pytest.raises(OSError, match="disk full"):
                write_agent_e2e_seed(tmp_path)
    assert "agent_e2e_seed_failed" in caplog.text
    storage.save_collection.assert_called_once()
    storage.save_environments.assert_not_called()


def test_seed_present_after_ready_via_identity(
    qapp: QApplication,
    seeded_agent_e2e_session: AgentAppSession,
) -> None:
    """FR2–FR4/FR8: after ready, seed is visible via tree model + env items."""
    assert QApplication.instance() is qapp
    session = seeded_agent_e2e_session
    assert session.window.is_ui_ready is True
    tree = session.window.findChild(QTreeView, COLLECTION_TREE)
    assert tree is not None
    collections, requests = _tree_texts(tree)
    assert SEED_COLLECTION_NAME in collections, collections
    assert f"GET {SEED_GET_REQUEST_NAME}" in requests, requests
    assert f"POST {SEED_POST_REQUEST_NAME}" in requests, requests

    selector = session.window.findChild(QComboBox, ENV_SELECTOR)
    assert selector is not None
    env_texts = _env_item_texts(selector)
    assert SEED_ENV_NAME in env_texts, env_texts
    assert selector.currentText() == "No Environment"


def test_seed_isolation_across_sessions(qapp: QApplication) -> None:
    """FR5/FR6: seeded state does not bleed into a blank second session."""
    assert QApplication.instance() is qapp
    with seeded_agent_dirs() as (config_a, data_a):
        with AgentAppSession(
            offscreen=True,
            config_dir=config_a,
            data_dir=data_a,
            ready_timeout=30.0,
        ) as seeded:
            assert seeded.window.is_ui_ready is True
            tree = seeded.window.findChild(QTreeView, COLLECTION_TREE)
            assert tree is not None
            collections, _ = _tree_texts(tree)
            assert SEED_COLLECTION_NAME in collections

    with TemporaryDirectory() as config_b, TemporaryDirectory() as data_b:
        with AgentAppSession(
            offscreen=True,
            config_dir=Path(config_b),
            data_dir=Path(data_b),
            ready_timeout=30.0,
        ) as blank:
            assert blank.window.is_ui_ready is True
            tree = blank.window.findChild(QTreeView, COLLECTION_TREE)
            assert tree is not None
            collections, _ = _tree_texts(tree)
            assert SEED_COLLECTION_NAME not in collections, collections
            selector = blank.window.findChild(QComboBox, ENV_SELECTOR)
            assert selector is not None
            assert SEED_ENV_NAME not in _env_item_texts(selector)
