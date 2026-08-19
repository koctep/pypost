"""MCP endpoint composition, persistence and lifecycle control (PYPOST-1071).

Extracted from ``MainWindow``: PYPOST-1044 placed multi-server registry construction,
persisted-configuration mutation and endpoint lifecycle commands into the composition
root, which is neither its documented responsibility nor a testable seam. The window now
composes this controller and keeps only the startup readiness gate.
"""
from __future__ import annotations

import logging
from typing import Callable, TYPE_CHECKING

from pypost.core.config_manager import ConfigManager
from pypost.core.mcp_activity_log import McpActivityEntry
from pypost.core.mcp_server_registry import MCPServerRegistry, McpServerStatus
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.core.qt.mcp_server import MCPServerManager
from pypost.core.template_service import TemplateService
from pypost.models.models import Collection, Environment
from pypost.models.settings import AppSettings, McpServerConfiguration

if TYPE_CHECKING:  # pragma: no cover - import cycle guard for the composition root
    from pypost.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class McpServerSettingsController:
    """Owns MCP composition, persisted endpoint rows, and per-instance lifecycle.

    ``settings_provider`` is a callable rather than a stored value because the composition
    root replaces its ``AppSettings`` instance whenever the settings dialog commits.
    """

    def __init__(
        self,
        *,
        settings_provider: Callable[[], AppSettings],
        config_manager: ConfigManager,
        collections_provider: Callable[[], object],
        get_collections: Callable[[], list[Collection]],
        environment_lookup: Callable[[str], Environment | None],
        metrics: MetricsTrackerProtocol,
        template_service: TemplateService,
        mcp_manager: MCPServerManager | None = None,
        registry: MCPServerRegistry | None = None,
    ) -> None:
        self._settings_provider = settings_provider
        self._config_manager = config_manager
        self._collections_provider = collections_provider
        self._get_collections = get_collections
        if mcp_manager is not None:
            logger.debug("mcp_manager_source source=injected")
            self.manager = mcp_manager
        else:
            logger.debug("mcp_manager_source source=new")
            self.manager = MCPServerManager(
                metrics=metrics, template_service=template_service
            )
        if registry is not None:
            logger.debug("mcp_registry_source source=injected")
            self.registry = registry
        else:
            logger.debug("mcp_registry_source source=new")
            self.registry = MCPServerRegistry(
                collection_lookup=self._collection_by_id,
                environment_lookup=environment_lookup,
                metrics=metrics,
                template_service=template_service,
            )
        self.registry.reconfiguration_finished.connect(
            self._on_mcp_server_reconfiguration_finished
        )
        self._load_persisted_mcp_servers()

    @classmethod
    def for_window(
        cls,
        window: MainWindow,
        *,
        mcp_manager: MCPServerManager | None = None,
        registry: MCPServerRegistry | None = None,
    ) -> McpServerSettingsController:
        """Wire the controller from the composition root's already-built collaborators."""
        return cls(
            settings_provider=lambda: window.settings,
            config_manager=window.config_manager,
            collections_provider=lambda: window.collections,
            get_collections=window.request_manager.get_collections,
            environment_lookup=lambda environment_id: window.env.environment_by_id(
                environment_id
            ),
            metrics=window.metrics,
            template_service=window.template_service,
            mcp_manager=mcp_manager,
            registry=registry,
        )

    # -- readiness gate and shutdown, driven by the composition root ------------------

    def start_enabled(self) -> None:
        """Start every enabled endpoint.

        The registry intentionally starts only after both stable ID sources are
        populated, so the composition root owns the call site. A missing collection or
        environment row fails independently inside the registry.
        """
        self.registry.start_enabled()

    def stop_all(self) -> None:
        self.registry.stop_all()

    # -- McpServerController protocol -------------------------------------------------

    def mcp_server_configurations(self) -> list[McpServerConfiguration]:
        """Return independent server rows from persisted application settings."""
        return [
            configuration.model_copy(deep=True)
            for configuration in self._settings.mcp_servers
        ]

    def mcp_server_count(self) -> int:
        """Return the number of configured server rows without copying them."""
        return len(self._settings.mcp_servers)

    def mcp_server_status(self, instance_id: str) -> McpServerStatus:
        """Return the current status for one configured endpoint."""
        return self.registry.status(instance_id)

    def mcp_server_activity(self, instance_id: str) -> list[McpActivityEntry]:
        """Return activity for only the requested instance, if it has started."""
        try:
            manager = self.registry.manager_for(instance_id)
        except KeyError:
            # An empty activity list otherwise looks identical to "endpoint never
            # started", which is the first question asked about a silent endpoint.
            logger.debug("mcp_server_activity_unavailable instance_id=%s", instance_id)
            return []
        return manager.activity_log.get_entries()

    def upsert_mcp_server(self, configuration: McpServerConfiguration) -> None:
        """Save one endpoint configuration without disturbing other endpoints."""
        try:
            previous = self._mcp_server_configuration(configuration.id)
        except KeyError:
            previous = None
        if previous is not None and self.registry.is_running(configuration.id):
            # A running row must use the registry's transactional replacement
            # path; merely persisting it would leave the old endpoint live.
            self.registry.reconfigure(configuration.id, configuration)
            return
        self.registry.upsert(configuration)
        reason = "update" if previous is not None else "create"
        configurations = {
            existing.id: existing.model_copy(deep=True)
            for existing in self._settings.mcp_servers
        }
        configurations[configuration.id] = configuration.model_copy(deep=True)
        self._settings.mcp_servers = list(configurations.values())
        self._save_mcp_server_configurations(reason)

    def remove_mcp_server(self, instance_id: str) -> None:
        """Stop and remove exactly one persisted endpoint."""
        self.registry.remove(instance_id)
        self._settings.mcp_servers = [
            configuration
            for configuration in self._settings.mcp_servers
            if configuration.id != instance_id
        ]
        self._save_mcp_server_configurations("remove")

    def start_mcp_server(self, instance_id: str) -> None:
        """Explicitly enable and launch one endpoint for this and future sessions."""
        configuration = self._mcp_server_configuration(instance_id)
        enabled = configuration.model_copy(update={"enabled": True})
        self.registry.upsert(enabled)
        self._replace_mcp_server_configuration(enabled, "start")
        self.registry.start(instance_id)

    def stop_mcp_server(self, instance_id: str) -> None:
        """Explicitly disable and stop one endpoint without touching its peers."""
        configuration = self._mcp_server_configuration(instance_id)
        disabled = configuration.model_copy(update={"enabled": False})
        self.registry.upsert(disabled)
        self._replace_mcp_server_configuration(disabled, "stop")
        self.registry.stop(instance_id)

    # -- internals --------------------------------------------------------------------

    @property
    def _settings(self) -> AppSettings:
        return self._settings_provider()

    def _collection_by_id(self, collection_id: str) -> Collection | None:
        """Use the collection presenter lookup, with a test-double-safe fallback."""
        lookup = getattr(self._collections_provider(), "collection_by_id", None)
        if callable(lookup):
            found: Collection | None = lookup(collection_id)
            return found
        return next(
            (
                collection
                for collection in self._get_collections()
                if collection.id == collection_id
            ),
            None,
        )

    def _on_mcp_server_reconfiguration_finished(
        self, instance_id: str, committed: bool
    ) -> None:
        """Persist a running-row edit only after its replacement endpoint binds."""
        # The registry already logs its own rollback; this line records the persistence
        # consequence, i.e. whether the user's edit survives the next restart.
        logger.info(
            "mcp_server_reconfigure_finished instance_id=%s committed=%s",
            instance_id,
            "true" if committed else "false",
        )
        if not committed:
            return
        configuration = next(
            (
                item
                for item in self.registry.list_configurations()
                if item.id == instance_id
            ),
            None,
        )
        if configuration is not None:
            self._replace_mcp_server_configuration(configuration, "reconfigure")

    def _load_persisted_mcp_servers(self) -> None:
        configurations = self._settings.mcp_servers
        for configuration in configurations:
            self.registry.upsert(configuration)
        # Counts only: ids, hosts and ports of individual endpoints stay out of the log.
        # This is the only startup evidence that persisted rows were restored at all,
        # and it separates "no endpoints configured" from "the readiness gate never ran".
        logger.info(
            "mcp_persisted_servers_loaded count=%d enabled_count=%d",
            len(configurations),
            sum(1 for configuration in configurations if configuration.enabled),
        )

    def _mcp_server_configuration(self, instance_id: str) -> McpServerConfiguration:
        for configuration in self._settings.mcp_servers:
            if configuration.id == instance_id:
                return configuration
        raise KeyError(f"Unknown MCP server instance: {instance_id}")

    def _replace_mcp_server_configuration(
        self, configuration: McpServerConfiguration, reason: str
    ) -> None:
        self._settings.mcp_servers = [
            configuration if existing.id == configuration.id else existing
            for existing in self._settings.mcp_servers
        ]
        self._save_mcp_server_configurations(reason)

    def _save_mcp_server_configurations(self, reason: str) -> None:
        """Persist the endpoint rows; ``reason`` names the mutation for operators.

        Logged before the write because ``ConfigManager.save_config`` swallows failures
        and reports them as its own ``config_save_failed`` ERROR — pairing the two lines
        is what identifies *which* MCP mutation was lost.
        """
        logger.info(
            "mcp_servers_persist_requested reason=%s count=%d",
            reason,
            len(self._settings.mcp_servers),
        )
        self._config_manager.save_config(self._settings)
