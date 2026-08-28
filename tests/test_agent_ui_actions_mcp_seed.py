"""PYPOST-993: Failing repro test for seed/collection injection in sidecar session.

Validates that:
1. Seed path resolution and environment variable precedence via ``pypost.agent.seed_loader``.
2. Sidecar CLI argument parsing for ``--seed`` and ``--seed-file`` in
   ``pypost.agent.ui_actions_mcp``.
3. In-process ``AgentAppSession`` initialization with ``seed_path`` and verification that seeded
   collections are loaded into the UI tree and visible in UI snapshot upon reaching ``is_ui_ready``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QTreeView

from pypost.agent.lifecycle import AgentAppSession
from pypost.agent.ui_actions_mcp import main
from pypost.ui.widget_ids import COLLECTION_TREE

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]


def _tree_texts(tree: QTreeView) -> tuple[list[str], list[str]]:
    """Extract top-level collection names and child request names from QTreeView."""
    model = tree.model()
    assert isinstance(model, QStandardItemModel)
    collections: list[str] = []
    requests: list[str] = []
    for row in range(model.rowCount()):
        col_item = model.item(row)
        if col_item is not None:
            collections.append(col_item.text())
            for child_row in range(col_item.rowCount()):
                child = col_item.child(child_row)
                if child is not None:
                    requests.append(child.text())
    return collections, requests


@pytest.mark.timeout(60)
def test_resolve_seed_path_cli_env_precedence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Resolve seed path giving precedence to CLI argument over environment variable."""
    from pypost.agent.seed_loader import DEFAULT_SEED_ENV_VAR, resolve_seed_path

    cli_path = tmp_path / "cli_seed.json"
    env_path = tmp_path / "env_seed.json"
    cli_path.touch()
    env_path.touch()

    # 1. CLI only
    monkeypatch.delenv(DEFAULT_SEED_ENV_VAR, raising=False)
    assert resolve_seed_path(cli_path=str(cli_path)) == cli_path
    assert resolve_seed_path(cli_path=cli_path) == cli_path

    # 2. Env var only
    monkeypatch.setenv(DEFAULT_SEED_ENV_VAR, str(env_path))
    assert resolve_seed_path(cli_path=None) == env_path

    # 3. CLI overrides env var
    assert resolve_seed_path(cli_path=str(cli_path)) == cli_path

    # 4. Neither provided
    monkeypatch.delenv(DEFAULT_SEED_ENV_VAR, raising=False)
    assert resolve_seed_path(cli_path=None) is None


@pytest.mark.timeout(60)
def test_ui_actions_mcp_cli_seed_argument_parsing(tmp_path: Path) -> None:
    """CLI argument --seed is parsed and forwarded to spawn session."""
    seed_file = tmp_path / "seed.json"
    seed_file.touch()

    with patch("pypost.agent.ui_actions_mcp._run_spawn_session") as mock_spawn:
        main(["--seed", str(seed_file)])
        mock_spawn.assert_called_once_with(
            offscreen=True,
            ready_timeout=30.0,
            seed_path=seed_file,
        )


@pytest.mark.timeout(60)
def test_ui_actions_mcp_cli_seed_file_alias(tmp_path: Path) -> None:
    """CLI argument alias --seed-file is accepted and passed to spawn session."""
    seed_file = tmp_path / "seed.json"
    seed_file.touch()

    with patch("pypost.agent.ui_actions_mcp._run_spawn_session") as mock_spawn:
        main(["--seed-file", str(seed_file)])
        mock_spawn.assert_called_once_with(
            offscreen=True,
            ready_timeout=30.0,
            seed_path=seed_file,
        )


@pytest.mark.timeout(60)
def test_ui_actions_mcp_cli_attach_with_seed_rejected(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Combining --attach with --seed is rejected because attach connects to running instance."""
    seed_file = tmp_path / "seed.json"
    seed_file.touch()

    with caplog.at_level(logging.ERROR, logger="pypost.agent.ui_actions_mcp"):
        with pytest.raises(SystemExit) as exc_info:
            main(["--attach", "--seed", str(seed_file)])
    assert exc_info.value.code == 1
    assert any(
        "agent_ui_mcp_attach_with_seed_rejected" in r.message
        and "error_type=CommandLineError" in r.message
        for r in caplog.records
    )


@pytest.mark.timeout(60)
def test_ui_actions_mcp_seed_failure_logged(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Invalid seed causes _run_spawn_session to log structured ERROR and exit(1)."""
    from pypost.agent.ui_actions_mcp import _run_spawn_session

    invalid_seed = tmp_path / "missing.json"
    with caplog.at_level(logging.ERROR, logger="pypost.agent.ui_actions_mcp"):
        with pytest.raises(SystemExit) as exc_info:
            _run_spawn_session(offscreen=True, ready_timeout=5.0, seed_path=invalid_seed)
    assert exc_info.value.code == 1
    assert any(
        "agent_ui_mcp_seed_failed" in r.message
        and "error_type=SeedLoadError" in r.message
        for r in caplog.records
    )


@pytest.mark.timeout(60)
def test_agent_app_session_with_seed_loads_collection_into_ui(
    tmp_path: Path,
) -> None:
    """AgentAppSession with seed_path pre-populates storage and renders in UI tree and snapshot."""
    seed_data = {
        "id": "repro-seed-collection-1",
        "name": "Repro Seed Collection",
        "requests": [
            {
                "id": "repro-seed-get-1",
                "name": "Repro GET",
                "method": "GET",
                "url": "https://example.test/repro-get",
            }
        ],
    }
    seed_file = tmp_path / "seed_collection.json"
    seed_file.write_text(json.dumps(seed_data), encoding="utf-8")

    session = AgentAppSession(seed_path=seed_file, offscreen=True, ready_timeout=30.0)
    with session:
        assert session.window.is_ui_ready is True

        # Verify collection tree widget contains seeded collection and request
        tree = session.window.findChild(QTreeView, COLLECTION_TREE)
        assert tree is not None, "Collection tree widget not found in MainWindow"
        collections, requests = _tree_texts(tree)
        assert "Repro Seed Collection" in collections
        assert any("Repro GET" in req for req in requests)

        # Verify UI snapshot reflects seeded collection
        snapshot = session.ui_snapshot()
        assert snapshot["role"] == "window"
        snapshot_text = json.dumps(snapshot)
        assert "Repro Seed Collection" in snapshot_text
