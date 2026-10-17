"""Reusable multi-subsystem integration harness helper and pytest fixture bindings.

Provides modular mixins and an isolated composite environment coordinating storage,
overlay management, library discovery, template rendering, runtime resolution,
and MCP server registry lifecycle.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import time
import types
from typing import Any
import pytest

from pypost.core.collection_serializer import read_collection_file
from pypost.core.collection_variable_import import (
    ConflictStrategy,
    ImportSummary,
    import_collection_variables_to_environment,
)
from pypost.core.library_connection_store import LibraryConnectionStore
from pypost.core.library_manager_service import LibraryManagerService
from pypost.core.library_runtime_resolver import LibraryRuntimeResolver
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.storage import StorageManager
from pypost.core.template_service import TemplateService
from pypost.models.collection_variable import CollectionVariable
from pypost.models.library_manifest import LocalLibraryOverlay
from pypost.models.models import Environment
from pypost.models.settings import McpServerConfiguration
from tests.helpers.port_allocation import allocate_tcp_port

logger = logging.getLogger(__name__)


@dataclass
class UnifiedLifecycleResult:
    """Outcome of end-to-end multi-subsystem workflow execution."""

    status: str
    standalone_server_id: str
    standalone_status: str
    imported_summary: ImportSummary
    rendered_request_url: str
    rendered_auth_header: str
    rendered_body: str


class LibraryFixtureMixin:
    """Mixin providing isolated catalog manifest, collection, and overlay management."""

    tmp_path: Path
    libraries_dir: Path
    overlay_dir: Path
    connection_store: LibraryConnectionStore
    overlay_manager: LocalOverlayManager
    library_service: LibraryManagerService
    runtime_resolver: LibraryRuntimeResolver

    def __init__(self, tmp_path: Path | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if tmp_path is not None and not hasattr(self, "libraries_dir"):
            self.init_library_fixture(tmp_path)

    def init_library_fixture(self, tmp_path: Path) -> None:
        """Initialize isolated filesystem directories and library services."""
        self.tmp_path = tmp_path
        self.libraries_dir = tmp_path / "libraries"
        self.overlay_dir = tmp_path / "libraries_data"
        self.libraries_dir.mkdir(parents=True, exist_ok=True)
        self.overlay_dir.mkdir(parents=True, exist_ok=True)

        self.connection_store = LibraryConnectionStore(self.tmp_path / "connections.json")
        self.overlay_manager = LocalOverlayManager(self.overlay_dir)
        self.library_service = LibraryManagerService(
            connection_store=self.connection_store,
            overlay_manager=self.overlay_manager,
        )
        self.runtime_resolver = LibraryRuntimeResolver(
            library_service=self.library_service,
            environment_lookup=lambda _id: None,
        )

    def create_library(
        self,
        manifest_id: str,
        is_legacy_manifest: bool = False,
        collections_data: dict[str, dict[str, Any]] | None = None,
        manifest_variables: list[CollectionVariable] | None = None,
        manifest_presets: dict[str, dict[str, Any]] | None = None,
    ) -> Path:
        """Create library directory with catalog or legacy manifest."""
        lib_dir = self.libraries_dir / manifest_id
        lib_dir.mkdir(parents=True, exist_ok=True)
        collections_dir = lib_dir / "collections"
        collections_dir.mkdir(parents=True, exist_ok=True)

        rel_paths = []
        if collections_data:
            for filename, col_dict in collections_data.items():
                col_path = collections_dir / filename
                rel_paths.append(f"collections/{filename}")
                if "id" not in col_dict:
                    col_dict["id"] = filename.split(".")[0]
                col_path.write_text(json.dumps(col_dict, indent=2), encoding="utf-8")

        manifest_dict: dict[str, Any] = {
            "id": manifest_id,
            "name": f"Library {manifest_id}",
            "version": "1.0.0" if is_legacy_manifest else "2.0.0",
            "collections": rel_paths,
        }
        if is_legacy_manifest:
            manifest_dict["variables"] = [v.model_dump() for v in (manifest_variables or [])]
            manifest_dict["presets"] = manifest_presets or {}

        manifest_file = lib_dir / "pypost-library.json"
        manifest_file.write_text(json.dumps(manifest_dict, indent=2), encoding="utf-8")

        self.library_service.connect_local_directory(lib_dir)
        logger.debug(
            "Created library manifest_id=%s version=%s collection_count=%d at %s",
            manifest_id,
            manifest_dict["version"],
            len(collections_data or {}),
            lib_dir,
        )
        return lib_dir

    def create_overlay(
        self,
        library_id: str,
        active_profile: str = "",
        secrets: dict[str, str] | None = None,
    ) -> LocalLibraryOverlay:
        """Create and persist a local library overlay."""
        overlay = LocalLibraryOverlay(
            library_id=library_id,
            active_profile=active_profile,
            secrets=dict(secrets) if secrets else {},
        )
        self.overlay_manager.save_overlay(overlay)
        logger.debug(
            "Created local library overlay for library_id=%s active_profile=%s "
            "secret_count=%d secret_keys=%s",
            library_id,
            active_profile,
            len(overlay.secrets),
            sorted(overlay.secrets.keys()),
        )
        return overlay


class EnvironmentFixtureMixin:
    """Mixin providing isolated workspace environment creation and storage management."""

    tmp_path: Path
    workspace_dir: Path
    storage_manager: StorageManager

    def __init__(self, tmp_path: Path | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if tmp_path is not None and not hasattr(self, "workspace_dir"):
            self.init_environment_fixture(tmp_path)

    def init_environment_fixture(self, tmp_path: Path) -> None:
        """Initialize isolated workspace directory and storage manager."""
        self.tmp_path = tmp_path
        self.workspace_dir = tmp_path / "workspace"
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.storage_manager = StorageManager(data_dir=self.workspace_dir)

    def create_workspace_environment(
        self,
        name: str = "Test Env",
        variables: dict[str, str] | None = None,
        hidden_keys: set[str] | None = None,
    ) -> Environment:
        """Create and persist an isolated workspace environment."""
        env = Environment(
            name=name,
            variables=variables or {},
            hidden_keys=hidden_keys or set(),
        )
        self.storage_manager.save_environments([env])
        logger.debug(
            "Created workspace environment name=%s variable_count=%d hidden_key_count=%d",
            name,
            len(env.variables),
            len(env.hidden_keys),
        )
        return env


class ServerRegistryFixtureMixin:
    """Mixin providing standalone MCP server candidate startup, readiness polling, and teardown."""

    registry: MCPServerRegistry
    template_service: TemplateService

    def __init__(
        self,
        *,
        registry: MCPServerRegistry | None = None,
        library_service: Any = None,
        template_service: TemplateService | None = None,
        tmp_path: Path | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if not hasattr(self, "registry"):
            self.init_server_registry_fixture(
                registry=registry,
                library_service=library_service,
                template_service=template_service,
            )

    def init_server_registry_fixture(
        self,
        *,
        registry: MCPServerRegistry | None = None,
        library_service: Any = None,
        template_service: TemplateService | None = None,
    ) -> None:
        """Initialize MCP server registry and template service."""
        self.template_service = (
            template_service
            if template_service is not None
            else getattr(self, "template_service", None) or TemplateService()
        )
        if registry is not None:
            self.registry = registry
        else:
            lib_svc = (
                library_service
                if library_service is not None
                else getattr(self, "library_service", None)
            )
            self.registry = MCPServerRegistry(
                library_service=lib_svc,
                environment_lookup=lambda _id: None,
                template_service=self.template_service,
            )

    def start_standalone_server(
        self,
        manifest_id: str,
        collection_id: str,
        collection_filename: str | None = None,
        collection_name: str | None = None,
        host: str = "127.0.0.1",
        port: int | None = None,
    ) -> tuple[str, int, str]:
        """Configure, validate, and start a standalone MCP server for a library collection."""
        col_filename = collection_filename or f"{collection_id}.json"
        display_name = collection_name or collection_id
        assigned_port = port if port is not None else allocate_tcp_port()
        server_id = f"standalone-{manifest_id}-{collection_id}"
        config = McpServerConfiguration.model_construct(
            id=server_id,
            name=f"Standalone {display_name}",
            host=host,
            port=assigned_port,
            server_type="local",
            library_id=manifest_id,
            manifest_id=manifest_id,
            library_collection_path=f"collections/{col_filename}",
            library_collection_index=0,
            environment_id=None,
            enabled=True,
        )
        logger.info(
            "Starting standalone MCP server server_id=%s manifest_id=%s port=%d",
            server_id,
            manifest_id,
            assigned_port,
        )
        try:
            self.registry.validate_library_candidate(config)
            self.registry.upsert(config)
            self.registry.start(config.id)
            self.registry.wait_for_state(config.id, "running", timeout=5.0)
            manager = self.registry._managers.get(config.id)
            if manager is not None:
                deadline = time.monotonic() + 5.0
                while time.monotonic() < deadline:
                    if manager.is_listening or manager.last_start_error:
                        break
                    time.sleep(0.02)
                if manager.last_start_error:
                    logger.error(
                        "Standalone MCP server server_id=%s reported startup error: %s",
                        server_id,
                        manager.last_start_error,
                    )
            status = self.registry.status(config.id).state
            logger.info(
                "Standalone MCP server server_id=%s reached state=%s",
                server_id,
                status,
            )
            return server_id, assigned_port, status
        except Exception as exc:
            logger.error(
                "Failed to start standalone MCP server server_id=%s: %s",
                server_id,
                exc,
            )
            raise

    def teardown(self) -> None:
        """Stop all running servers in registry and release active resources."""
        logger.info("Tearing down harness and stopping all registered servers")
        try:
            if hasattr(self, "registry") and self.registry is not None:
                self.registry.stop_all()
            logger.debug("Harness teardown completed successfully")
        except Exception as exc:
            logger.warning("Error stopping servers during harness teardown: %s", exc)

    def close(self) -> None:
        """Alias for teardown() supporting explicit resource close semantics."""
        self.teardown()

    def __enter__(self) -> ServerRegistryFixtureMixin:
        """Enter context manager, returning mixin instance."""
        logger.debug("Entered server registry fixture context manager scope")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit context manager, ensuring all running servers are stopped."""
        if exc_type is not None:
            logger.error(
                "Server registry fixture context manager exiting due to exception: %s: %s",
                exc_type.__name__,
                exc_val,
            )
        else:
            logger.debug("Exited server registry fixture context manager scope normally")
        self.teardown()


class CollectionVariablesIntegrationHarness(
    LibraryFixtureMixin,
    EnvironmentFixtureMixin,
    ServerRegistryFixtureMixin,
):
    """Encapsulates isolated filesystem, configuration stores, and service instances

    for end-to-end integration and compatibility matrix validation.
    """

    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.init_library_fixture(tmp_path)
        self.init_environment_fixture(tmp_path)
        self.template_service = TemplateService()
        self.init_server_registry_fixture(
            library_service=self.library_service,
            template_service=self.template_service,
        )
        logger.debug(
            "Initialized CollectionVariablesIntegrationHarness at root=%s",
            self.tmp_path,
        )

    def __enter__(self) -> CollectionVariablesIntegrationHarness:
        """Enter context manager, returning harness instance."""
        logger.debug("Entered harness context manager scope")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit context manager, ensuring all running servers are stopped."""
        if exc_type is not None:
            logger.error(
                "Harness context manager exiting due to exception: %s: %s",
                exc_type.__name__,
                exc_val,
            )
        else:
            logger.debug("Exited harness context manager scope normally")
        self.teardown()

    def teardown(self) -> None:
        """Stop all running servers in registry and release active resources."""
        super().teardown()

    def close(self) -> None:
        """Alias for teardown() supporting explicit resource close semantics."""
        self.teardown()

    def run_unified_lifecycle(
        self,
        *,
        manifest_id: str,
        collection_data: dict[str, Any],
        active_profile: str,
        overlay_secrets: dict[str, str],
        workspace_env_name: str,
        conflict_strategy: ConflictStrategy,
    ) -> UnifiedLifecycleResult:
        """Execute full unified multi-subsystem workflow orchestration:

        catalog discovery -> standalone MCP server startup -> collection copy ->
        workspace environment import -> template substitution.
        """
        collection_id = collection_data.get("id", "collection")
        col_filename = f"{collection_id}.json"
        logger.info(
            "Starting unified multi-subsystem lifecycle for manifest_id=%s "
            "collection_id=%s profile=%s conflict_strategy=%s",
            manifest_id,
            collection_id,
            active_profile,
            getattr(conflict_strategy, "value", conflict_strategy),
        )

        try:
            # 1. Connect library to library_service (via create_library)
            lib_dir = self.create_library(
                manifest_id=manifest_id,
                is_legacy_manifest=False,
                collections_data={col_filename: collection_data},
            )

            # 2. Save overlay secrets into overlay_manager
            if overlay_secrets or active_profile:
                self.create_overlay(
                    library_id=manifest_id,
                    active_profile=active_profile,
                    secrets=overlay_secrets,
                )

            # 3. Register and start standalone server in registry
            server_id, _, standalone_status = self.start_standalone_server(
                manifest_id=manifest_id,
                collection_id=collection_id,
                collection_filename=col_filename,
                collection_name=collection_data.get("name", collection_id),
            )

            # 4. Import collection variables into a workspace environment
            env = self.create_workspace_environment(name=workspace_env_name)
            col_file_path = lib_dir / "collections" / col_filename
            collection = read_collection_file(col_file_path)
            summary = import_collection_variables_to_environment(
                environment=env,
                collection=collection,
                conflict_strategy=conflict_strategy,
                preset_name=active_profile,
            )

            # 5. Build context combining environment variables and template variables
            context: dict[str, Any] = dict(env.variables)

            # 6. Render request URL, headers, and body with template_service
            req = collection.requests[0] if collection.requests else None
            rendered_url = ""
            rendered_auth = ""
            rendered_body = ""
            if req is not None:
                rendered_url = self.template_service.render_string(req.url, context)
                auth_header = req.headers.get("Authorization", "")
                rendered_auth = self.template_service.render_string(auth_header, context)
                rendered_body = self.template_service.render_string(req.body, context)

            logger.info(
                "Completed unified multi-subsystem lifecycle for manifest_id=%s "
                "server_id=%s (imported %d variables)",
                manifest_id,
                server_id,
                summary.total_imported,
            )

            return UnifiedLifecycleResult(
                status="success",
                standalone_server_id=server_id,
                standalone_status=standalone_status,
                imported_summary=summary,
                rendered_request_url=rendered_url,
                rendered_auth_header=rendered_auth,
                rendered_body=rendered_body,
            )
        except Exception as exc:
            logger.error(
                "Unified multi-subsystem lifecycle failed for manifest_id=%s collection_id=%s: %s",
                manifest_id,
                collection_id,
                exc,
            )
            raise


def _collection_integration_harness_impl(
    tmp_path: Path,
) -> Iterator[CollectionVariablesIntegrationHarness]:
    logger.debug("Pytest fixture yielding collection_integration_harness for %s", tmp_path)
    harness = CollectionVariablesIntegrationHarness(tmp_path)
    try:
        yield harness
    finally:
        logger.debug("Pytest fixture tearing down collection_integration_harness for %s", tmp_path)
        harness.teardown()


_fix = pytest.fixture(_collection_integration_harness_impl)


class _CallableFixture(type(_fix)):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._fixture_function(*args, **kwargs)


_fix.__class__ = _CallableFixture
collection_integration_harness = _fix


collection_harness = collection_integration_harness

__all__ = [
    "CollectionVariablesIntegrationHarness",
    "EnvironmentFixtureMixin",
    "LibraryFixtureMixin",
    "ServerRegistryFixtureMixin",
    "UnifiedLifecycleResult",
    "collection_harness",
    "collection_integration_harness",
]
