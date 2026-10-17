"""Automated failing repro test for In-Memory Virtual Filesystem Backend (PYPOST-1435).

Asserts the contracts and specifications in ai-tasks/PYPOST-1435/20-architecture.md:
- Standalone importability of InMemoryVirtualFS and in-memory storage adapters.
- In-memory node hierarchy and transparent pathlib.Path method interception with zero disk I/O.
- CollectionVariablesIntegrationHarness initialization with in_memory=True
  and zero physical disk I/O.
- Backward compatibility of CollectionVariablesIntegrationHarness with physical tmp_path.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
import pytest

from pypost.core.collection_variable_import import ConflictStrategy
from pypost.models.library_manager import LibraryConnectionRecord, LibrarySourceType
from pypost.models.library_manifest import LocalLibraryOverlay
from pypost.models.models import Environment
from tests.helpers.collection_integration_harness import (
    CollectionVariablesIntegrationHarness,
    UnifiedLifecycleResult,
)
from tests.helpers.in_memory_virtual_fs import (
    InMemoryLibraryConnectionStore,
    InMemoryLocalOverlayManager,
    InMemoryStorageManager,
    InMemoryVirtualFS,
    VirtualFile,
)

pytestmark = pytest.mark.timeout(30)


@pytest.mark.timeout(30)
def test_in_memory_virtual_fs_tree_and_interception() -> None:
    """Validate virtual filesystem node tree, operations, and Path interception with zero I/O."""
    vfs = InMemoryVirtualFS()
    with vfs:
        v_dir = vfs.root_path / "sub" / "nested"
        v_dir.mkdir(parents=True, exist_ok=True)
        v_file = v_dir / "sample.txt"
        v_file.write_text("hello in-memory world", encoding="utf-8")

        assert v_file.exists()
        assert v_file.is_file()
        assert not v_file.is_dir()
        assert v_dir.exists()
        assert v_dir.is_dir()
        assert v_file.read_text(encoding="utf-8") == "hello in-memory world"

        children = list(v_dir.iterdir())
        assert len(children) == 1
        assert children[0].name == "sample.txt"

        globbed = list(vfs.root_path.glob("**/*.txt"))
        assert len(globbed) == 1
        assert globbed[0].name == "sample.txt"

        v_file.unlink()
        assert not v_file.exists()

    # Zero disk I/O verification: physical host filesystem has no trace of virtual root
    assert not os.path.exists(str(vfs.root_path))


@pytest.mark.timeout(30)
def test_in_memory_virtual_storage_adapters() -> None:
    """Validate in-memory adapters for StorageManager, OverlayManager, and ConnectionStore."""
    vfs = InMemoryVirtualFS()
    with vfs:
        # 1. InMemoryLibraryConnectionStore
        conn_path = vfs.root_path / "connections.json"
        conn_store = InMemoryLibraryConnectionStore(vfs=vfs, path=conn_path)
        record = LibraryConnectionRecord(
            id="conn-1",
            name="Test Connection",
            source_type=LibrarySourceType.LOCAL_DIRECTORY,
            source_path=str(vfs.root_path / "lib1"),
        )
        conn_store.add(record)
        loaded_conns = conn_store.load()
        assert len(loaded_conns) == 1
        assert loaded_conns[0].id == "conn-1"

        # 2. InMemoryLocalOverlayManager
        overlay_dir = vfs.root_path / "overlays"
        overlay_mgr = InMemoryLocalOverlayManager(vfs=vfs, base_dir=overlay_dir)
        overlay = LocalLibraryOverlay(library_id="lib1", active_profile="staging")
        overlay_mgr.save_overlay(overlay)
        loaded_overlay = overlay_mgr.get_overlay("lib1")
        assert loaded_overlay.library_id == "lib1"
        assert loaded_overlay.active_profile == "staging"

        # 3. InMemoryStorageManager
        storage_dir = vfs.root_path / "workspace"
        storage_mgr = InMemoryStorageManager(vfs=vfs, data_dir=storage_dir)
        env = Environment(id="env-1", name="Staging Env", values={"KEY": "val"})
        storage_mgr.save_environments([env])
        loaded_envs = storage_mgr.load_environments()
        assert len(loaded_envs) == 1
        assert loaded_envs[0].name == "Staging Env"

    # Assert no physical paths created on disk
    assert not os.path.exists(str(vfs.root_path))


@pytest.mark.timeout(30)
def test_collection_harness_in_memory_mode() -> None:
    """Validate in-memory harness initialization, entity creation, and lifecycle execution."""
    col_dict = {
        "id": "col-vfs-1",
        "name": "Virtual FS Test Collection",
        "variables": [
            {
                "name": "api_host",
                "type": "string",
                "default": "vfs.example.internal",
                "required": True,
                "secret": False,
            }
        ],
        "requests": [
            {
                "name": "health",
                "url": "https://{{api_host}}/health",
                "method": "GET",
                "headers": {},
                "body": None,
            }
        ],
    }

    with CollectionVariablesIntegrationHarness(in_memory=True) as harness:
        assert getattr(harness, "in_memory", False) is True
        assert getattr(harness, "virtual_fs", None) is not None

        # Create library, overlay, and workspace environment in memory
        manifest_path = harness.create_library(
            manifest_id="lib-vfs-test",
            collections_data={"col.json": col_dict},
        )
        assert harness.virtual_fs.exists(manifest_path)

        overlay = harness.create_overlay(
            library_id="lib-vfs-test",
            active_profile="dev",
            variable_overrides={"api_host": "override.example.internal"},
        )
        assert overlay.library_id == "lib-vfs-test"

        env = harness.create_workspace_environment(
            name="Integration Env",
            variables={"api_host": "env.example.internal"},
        )
        assert env.name == "Integration Env"

        # Execute unified lifecycle
        result: UnifiedLifecycleResult = harness.run_unified_lifecycle(
            manifest_id="lib-vfs-test",
            target_env_id=env.id,
            col_filename="col.json",
            conflict_strategy=ConflictStrategy.OVERWRITE,
        )
        assert result.status == "success"
        assert result.catalog_entry is not None
        assert result.rendered_request is not None
        assert "override.example.internal" in result.rendered_request["url"]


@pytest.mark.timeout(30)
def test_in_memory_zero_disk_io_verification() -> None:
    """Validate zero physical disk I/O during in-memory harness operations."""
    harness = CollectionVariablesIntegrationHarness(in_memory=True)
    try:
        virtual_root = harness.tmp_path
        assert not os.path.exists(str(virtual_root))

        harness.create_library(
            manifest_id="lib-zero-io",
            collections_data={"sample.json": {"id": "col-zero", "name": "Zero Col"}},
        )
        assert not os.path.exists(str(virtual_root))
        assert not os.path.exists(f"/tmp/{virtual_root.name}")
    finally:
        harness.teardown()

    assert not os.path.exists(str(virtual_root))


@pytest.mark.timeout(30)
def test_collection_harness_backward_compatibility(tmp_path: Path) -> None:
    """Validate backward compatibility of CollectionVariablesIntegrationHarness with tmp_path."""
    with CollectionVariablesIntegrationHarness(tmp_path=tmp_path) as harness:
        assert harness.tmp_path == tmp_path
        assert harness.libraries_dir.is_dir()
        assert harness.workspace_dir.is_dir()
        assert harness.overlay_dir.is_dir()
        assert os.path.exists(str(tmp_path))


@pytest.mark.timeout(30)
def test_in_memory_virtual_fs_logging_levels(caplog: pytest.LogCaptureFixture) -> None:
    """Validate syslog-compatible logging severity levels for virtual filesystem."""
    vfs = InMemoryVirtualFS()

    with caplog.at_level(logging.DEBUG, logger="tests.helpers.in_memory_virtual_fs"):
        with vfs:
            # Lifecycle transitions (INFO)
            assert any(
                r.levelno == logging.INFO and "Mounted InMemoryVirtualFS" in r.message
                for r in caplog.records
            )

            # Node operations (DEBUG)
            target = vfs.root_path / "obs_test.txt"
            target.write_text("obs payload", encoding="utf-8")
            assert any(
                r.levelno == logging.DEBUG and "write_text path=" in r.message
                for r in caplog.records
            )

            _ = target.read_text(encoding="utf-8")
            assert any(
                r.levelno == logging.DEBUG and "read_text path=" in r.message
                for r in caplog.records
            )

            # Idempotent cleanup of missing node (WARNING)
            missing = vfs.root_path / "nonexistent.txt"
            vfs.unlink(missing, missing_ok=True)
            assert any(
                r.levelno == logging.WARNING
                and "Virtual file missing on unlink" in r.message
                for r in caplog.records
            )

        # Unmount transition (INFO)
        assert any(
            r.levelno == logging.INFO and "Unmounted InMemoryVirtualFS" in r.message
            for r in caplog.records
        )


@pytest.mark.timeout(30)
def test_in_memory_virtual_fs_metrics() -> None:
    """Validate operational metrics and resource counters for virtual filesystem."""
    vfs = InMemoryVirtualFS()
    initial_metrics = vfs.get_metrics()
    assert initial_metrics["mcp.harness.virtual_fs.ops_total"] == 0
    assert initial_metrics["mcp.harness.virtual_fs.nodes_count"] == 1
    assert initial_metrics["mcp.harness.virtual_fs.bytes_total"] == 0

    with vfs:
        folder = vfs.root_path / "data"
        folder.mkdir(parents=True, exist_ok=True)
        file_path = folder / "test.json"
        payload = '{"key": "value"}'
        file_path.write_text(payload, encoding="utf-8")
        _ = file_path.read_text(encoding="utf-8")
        _ = file_path.exists()
        _ = file_path.stat()
        _ = list(folder.iterdir())
        _ = list(vfs.root_path.glob("**/*.json"))

        metrics = vfs.get_metrics()
        assert metrics["mcp.harness.virtual_fs.ops_total"] >= 7
        assert metrics["mcp.harness.virtual_fs.nodes_count"] == 3  # root + data + test.json
        assert metrics["mcp.harness.virtual_fs.bytes_total"] == len(payload.encode("utf-8"))
        by_type = metrics["mcp.harness.virtual_fs.ops_by_type"]
        assert by_type["mkdir"] >= 1
        assert by_type["write_text"] >= 1
        assert by_type["read_text"] >= 1
        assert by_type["exists"] >= 1
        assert by_type["stat"] >= 1
        assert by_type["iterdir"] >= 1
        assert by_type["glob"] >= 1

    vfs.clear()
    cleared = vfs.get_metrics()
    assert cleared["mcp.harness.virtual_fs.ops_total"] == 0
    assert cleared["mcp.harness.virtual_fs.nodes_count"] == 1
    assert cleared["mcp.harness.virtual_fs.bytes_total"] == 0


@pytest.mark.timeout(30)
def test_in_memory_virtual_fs_corruption_error_logging(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Validate error-level log capture when virtual hierarchy corruption is encountered."""
    vfs = InMemoryVirtualFS()
    # Artificially inject a non-directory node where a directory is traversed
    vfs._root_node.children["invalid_parent"] = VirtualFile(name="invalid_parent")

    with caplog.at_level(logging.ERROR, logger="tests.helpers.in_memory_virtual_fs"):
        # Traversal through invalid_parent/subfile must detect non-VirtualDir and log ERROR
        found = vfs._find_node(vfs.root_path / "invalid_parent" / "subfile")
        assert found is None

    assert any(
        r.levelno == logging.ERROR
        and "Virtual filesystem hierarchy corruption" in r.message
        for r in caplog.records
    )
