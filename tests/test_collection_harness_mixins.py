"""Failing repro test asserting modular harness architecture and mixin decomposition.

Validates the modular contracts specified in ai-tasks/PYPOST-1433/20-architecture.md:
- Standalone importability and initialization of LibraryFixtureMixin.
- Standalone importability and initialization of EnvironmentFixtureMixin.
- Standalone importability and initialization of ServerRegistryFixtureMixin.
- Cooperative multiple inheritance and backward compatibility of
  CollectionVariablesIntegrationHarness.
- Partial custom composition of mixins without server registry dependencies.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from pypost.models.settings import McpServerConfiguration
from tests.helpers.collection_integration_harness import (
    LibraryFixtureMixin,
    EnvironmentFixtureMixin,
    ServerRegistryFixtureMixin,
    CollectionVariablesIntegrationHarness,
)

pytestmark = pytest.mark.timeout(30)


@pytest.mark.timeout(30)
def test_harness_mixins_inheritance_and_exports() -> None:
    """Validate that CollectionVariablesIntegrationHarness subclasses all three mixins."""
    assert issubclass(CollectionVariablesIntegrationHarness, LibraryFixtureMixin)
    assert issubclass(CollectionVariablesIntegrationHarness, EnvironmentFixtureMixin)
    assert issubclass(CollectionVariablesIntegrationHarness, ServerRegistryFixtureMixin)


@pytest.mark.timeout(30)
def test_standalone_library_fixture_mixin(tmp_path: Path) -> None:
    """Validate standalone LibraryFixtureMixin initialization, manifest, and overlay creation."""
    lib_fix = LibraryFixtureMixin(tmp_path)
    assert lib_fix.tmp_path == tmp_path
    assert lib_fix.libraries_dir.is_dir()
    assert lib_fix.overlay_dir.is_dir()
    assert lib_fix.connection_store is not None
    assert lib_fix.overlay_manager is not None
    assert lib_fix.library_service is not None
    assert lib_fix.runtime_resolver is not None

    # Assert decoupling from storage and server registry
    assert not hasattr(lib_fix, "workspace_dir")
    assert not hasattr(lib_fix, "storage_manager")
    assert not hasattr(lib_fix, "registry")

    # Assert manifest and collection creation
    manifest_path = lib_fix.create_library(
        manifest_id="lib-standalone",
        is_legacy_manifest=False,
        collections_data={
            "col-standalone.json": {
                "id": "col-standalone",
                "name": "Standalone Col",
                "variables": [],
                "requests": [],
            }
        },
    )
    assert manifest_path.is_dir()
    assert (manifest_path / "pypost-library.json").is_file()
    col_path = lib_fix.libraries_dir / "lib-standalone" / "collections" / "col-standalone.json"
    assert col_path.is_file()

    # Assert overlay persistence
    overlay = lib_fix.create_overlay(
        library_id="lib-standalone",
        active_profile="staging",
        secrets={"api_token": "secret_standalone_token"},
    )
    assert overlay.library_id == "lib-standalone"
    assert overlay.active_profile == "staging"
    assert overlay.secrets == {"api_token": "secret_standalone_token"}


@pytest.mark.timeout(30)
def test_standalone_environment_fixture_mixin(tmp_path: Path) -> None:
    """Validate standalone EnvironmentFixtureMixin initialization and environment persistence."""
    env_fix = EnvironmentFixtureMixin(tmp_path)
    assert env_fix.tmp_path == tmp_path
    assert env_fix.workspace_dir.is_dir()
    assert env_fix.storage_manager is not None

    # Assert decoupling from libraries and server registry
    assert not hasattr(env_fix, "libraries_dir")
    assert not hasattr(env_fix, "overlay_dir")
    assert not hasattr(env_fix, "registry")

    # Assert environment creation and persistence
    env = env_fix.create_workspace_environment(
        name="Standalone Test Env",
        variables={"BASE_URL": "https://example.com"},
        hidden_keys={"BASE_URL"},
    )
    assert env.name == "Standalone Test Env"
    assert env.get_value("BASE_URL") == "https://example.com"
    saved = env_fix.storage_manager.load_environments()
    assert any(e.name == "Standalone Test Env" for e in saved)


@pytest.mark.timeout(30)
def test_standalone_server_registry_fixture_mixin() -> None:
    """Validate standalone ServerRegistryFixtureMixin lifecycle and candidate management."""
    with ServerRegistryFixtureMixin() as server_fix:
        assert server_fix.registry is not None
        assert server_fix.template_service is not None

        # Assert decoupling from filesystem paths
        assert not hasattr(server_fix, "libraries_dir")
        assert not hasattr(server_fix, "workspace_dir")
        assert not hasattr(server_fix, "overlay_dir")

        # Register server candidate
        config = McpServerConfiguration.model_construct(
            id="standalone-candidate-1",
            name="Standalone Candidate",
            host="127.0.0.1",
            port=9999,
            server_type="local",
            enabled=True,
        )
        server_fix.registry.upsert(config)
        assert server_fix.registry.get_config("standalone-candidate-1") is not None

    # Teardown and close should be idempotent
    server_fix.teardown()
    server_fix.close()


@pytest.mark.timeout(30)
def test_partial_custom_composition(tmp_path: Path) -> None:
    """Validate custom fixture composing LibraryFixtureMixin and EnvironmentFixtureMixin."""
    class CustomLibraryAndStorageFixture(LibraryFixtureMixin, EnvironmentFixtureMixin):
        def __init__(self, path: Path) -> None:
            self.init_library_fixture(path)
            self.init_environment_fixture(path)

    custom = CustomLibraryAndStorageFixture(tmp_path)
    assert custom.libraries_dir.is_dir()
    assert custom.overlay_dir.is_dir()
    assert custom.workspace_dir.is_dir()
    assert custom.library_service is not None
    assert custom.storage_manager is not None
    assert not hasattr(custom, "registry")


@pytest.mark.timeout(30)
def test_composite_harness_inheritance_and_backward_compatibility(tmp_path: Path) -> None:
    """Validate that CollectionVariablesIntegrationHarness satisfies all mixin contracts."""
    harness = CollectionVariablesIntegrationHarness(tmp_path)
    assert isinstance(harness, LibraryFixtureMixin)
    assert isinstance(harness, EnvironmentFixtureMixin)
    assert isinstance(harness, ServerRegistryFixtureMixin)
    assert harness.tmp_path == tmp_path
    assert harness.libraries_dir.is_dir()
    assert harness.workspace_dir.is_dir()
    assert harness.overlay_dir.is_dir()
    assert harness.storage_manager is not None
    assert harness.connection_store is not None
    assert harness.overlay_manager is not None
    assert harness.template_service is not None
    assert harness.library_service is not None
    assert harness.runtime_resolver is not None
    assert harness.registry is not None
    harness.teardown()
