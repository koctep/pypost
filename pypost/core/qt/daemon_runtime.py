from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Mapping

from PySide6.QtCore import QCoreApplication, QObject, QTimer

from pypost.core.config_manager import ConfigManager, StrictConfigError
from pypost.core.daemon_config import ResolvedDaemonPaths
from pypost.core.daemon_storage import DaemonDataError
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.qt.metrics import MetricsManager
from pypost.core.storage import StorageManager
from pypost.core.template_service import TemplateService
from pypost.models.settings import McpServerConfiguration

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RequiredDataConsumers:
    collections: Mapping[str, tuple[str, ...]]
    environments: Mapping[str, tuple[str, ...]]


def build_required_data_consumers(
    configurations: list[McpServerConfiguration],
) -> RequiredDataConsumers:
    collections: dict[str, set[str]] = {}
    environments: dict[str, set[str]] = {}
    for configuration in configurations:
        if not configuration.enabled:
            continue
        if configuration.server_type == "local" and configuration.collection_id:
            collections.setdefault(configuration.collection_id, set()).add(configuration.id)
        if configuration.environment_id:
            environments.setdefault(configuration.environment_id, set()).add(configuration.id)
    return RequiredDataConsumers(
        collections={key: tuple(sorted(value)) for key, value in collections.items()},
        environments={key: tuple(sorted(value)) for key, value in environments.items()},
    )


def affected_server_ids(
    error: DaemonDataError,
    consumers: RequiredDataConsumers,
) -> tuple[str, ...]:
    index = consumers.collections if error.kind == "collections" else consumers.environments
    if error.record_id is not None:
        return index.get(error.record_id, ())
    return tuple(sorted({server_id for server_ids in index.values() for server_id in server_ids}))


class DaemonStartupError(Exception):
    pass


class DaemonRuntime(QObject):
    def __init__(
        self,
        paths: ResolvedDaemonPaths,
        *,
        startup_timeout_ms: int = 10_000,
        config_manager: ConfigManager | None = None,
        storage: StorageManager | None = None,
        metrics: MetricsManager | None = None,
    ) -> None:
        super().__init__()
        self._paths = paths
        self._startup_timeout_ms = startup_timeout_ms
        self._config_manager = config_manager or ConfigManager()
        self._storage = storage
        self._metrics = metrics
        self._registry: MCPServerRegistry | None = None
        self._enabled_ids: tuple[str, ...] = ()
        self._ready = False
        self._exit_code = 0
        self._shutting_down = False
        self._deadline = QTimer(self)
        self._deadline.setSingleShot(True)
        self._deadline.timeout.connect(lambda: self._fail("startup_timeout"))

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def exit_code(self) -> int:
        return self._exit_code

    def start(self) -> None:
        try:
            settings = self._config_manager.load_config_strict()
            enabled = [row for row in settings.mcp_servers if row.enabled]
            consumers = build_required_data_consumers(enabled)
            storage = self._storage or StorageManager(
                collections_dir=self._paths.collections_dir,
                environments_dir=self._paths.environments_dir,
                initialize_collections=self._paths.collections_source == "default",
                initialize_environments=self._paths.environments_source == "default",
            )
            storage.apply_encryption_settings(settings)
            try:
                collections = storage.load_collections_snapshot_strict(
                    required_ids=set(consumers.collections)
                )
                environments = storage.load_environments_snapshot_strict(
                    required_ids=set(consumers.environments)
                )
            except DaemonDataError as exc:
                server_ids = affected_server_ids(exc, consumers)
                for server_id in server_ids or ("none",):
                    logger.error(
                        "daemon_data_failed kind=%s category=%s affected_server_id=%s",
                        exc.kind,
                        exc.category,
                        server_id,
                    )
                raise DaemonStartupError(
                    f"{exc.kind} category={exc.category} "
                    f"affected_count={len(server_ids)}"
                ) from exc
            metrics = self._metrics or MetricsManager()
            registry = MCPServerRegistry(
                collection_lookup=collections.get,
                environment_lookup=environments.get,
                metrics=metrics,
                template_service=TemplateService(metrics),
            )
            for configuration in enabled:
                registry.upsert(configuration.model_copy(deep=True))
            self._storage = storage
            self._metrics = metrics
            self._registry = registry
            self._enabled_ids = tuple(configuration.id for configuration in enabled)
            metrics.listening_changed.connect(lambda _value: self._check_ready())
            metrics.unexpected_exit.connect(
                lambda reason: self._fail(f"metrics_{reason}")
            )
            metrics.connect_start_failed(lambda _message: self._fail("metrics_start_failed"))
            registry.status_changed.connect(self._on_registry_status)
            self._deadline.start(self._startup_timeout_ms)
            metrics.start_server(settings.metrics_host, settings.metrics_port)
            if self._shutting_down:
                return
            registry.start_enabled()
            self._check_ready()
        except (DaemonStartupError, StrictConfigError) as exc:
            logger.error("daemon_start_failed %s", exc)
            self._fail("configuration")
        except Exception as exc:
            logger.error("daemon_start_failed category=%s", type(exc).__name__)
            self._fail("configuration")

    def _on_registry_status(self, instance_id: str, state: str, _message: str) -> None:
        if state == "failed":
            self._fail(f"mcp_failed instance_id={instance_id}")
            return
        if self._ready and state == "stopped" and not self._shutting_down:
            self._fail(f"mcp_stopped instance_id={instance_id}")
            return
        self._check_ready()

    def _check_ready(self) -> None:
        if self._shutting_down or self._metrics is None or self._registry is None:
            return
        states = {status.id: status.state for status in self._registry.list_statuses()}
        if self._metrics.is_listening and all(
            states.get(instance_id) == "running" for instance_id in self._enabled_ids
        ):
            self._deadline.stop()
            if not self._ready:
                self._ready = True
                logger.info("daemon_ready enabled_servers=%d", len(self._enabled_ids))

    def _fail(self, reason: str) -> None:
        if self._shutting_down:
            return
        self._exit_code = 1
        logger.error("daemon_fatal reason=%s", reason)
        self.shutdown()
        application = QCoreApplication.instance()
        if application is not None:
            application.quit()

    def shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        self._deadline.stop()
        if self._registry is not None:
            try:
                self._registry.stop_all()
            except Exception as exc:
                self._exit_code = 1
                logger.error("daemon_mcp_shutdown_failed category=%s", type(exc).__name__)
        if self._metrics is not None:
            try:
                self._metrics.stop_server()
            except Exception as exc:
                self._exit_code = 1
                logger.error("daemon_metrics_shutdown_failed category=%s", type(exc).__name__)
        self._ready = False
