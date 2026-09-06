"""MCP endpoint composition, persistence and lifecycle control (PYPOST-1071).

Extracted from ``MainWindow``: PYPOST-1044 placed multi-server registry construction,
persisted-configuration mutation and endpoint lifecycle commands into the composition
root, which is neither its documented responsibility nor a testable seam. The window now
composes this controller and keeps only the startup readiness gate.
"""
from __future__ import annotations

import logging
import json
import os
import shutil
import time
import uuid
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from pypost.core.config_manager import ConfigManager
from pypost.core.mcp_activity_log import McpActivityEntry
from pypost.core.mcp_server_registry import MCPServerRegistry, McpServerStatus
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.qt.mcp_server import MCPServerManager
from pypost.core.template_service import TemplateService
from pypost.models.library_manifest import LocalLibraryOverlay
from pypost.models.models import Collection, Environment
from pypost.models.settings import AppSettings, McpServerConfiguration

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SaveResult:
    committed: bool
    category: str = ""
    safe_message: str = ""


@dataclass(frozen=True)
class RollbackResult:
    restored: bool
    category: str = ""
    safe_message: str = ""


class CheckedSettingsStore:
    """Small checked in-memory store used by library MCP saves and tests."""

    def __init__(self, *, root: Path | str | None = None, fail_commit: bool = False):
        self.root = Path(root) if root is not None else None
        self.fail_commit = fail_commit
        self._snapshot: dict = {}
        self.overlay_write_count = 0
        self.handles_overlay = False

    def commit(
        self, candidate_settings: dict, candidate_overlay: dict, expected_previous: dict,
        expected_previous_overlay=None,
    ) -> SaveResult:
        if self.fail_commit:
            self._snapshot = deepcopy(expected_previous)
            return SaveResult(
                False,
                "persistence_failure",
                "MCP library settings could not be saved",
            )
        self._snapshot = {
            "server": deepcopy(candidate_settings),
            "overlay": deepcopy(candidate_overlay),
        }
        self.overlay_write_count += 1
        return SaveResult(True)

    def read_snapshot(self) -> dict:
        return deepcopy(self._snapshot)

    def restore(self, snapshot: dict, _overlay_snapshot=None) -> RollbackResult:
        self._snapshot = deepcopy(snapshot)
        return RollbackResult(True)


class ConfigManagerSettingsStore:
    """Checked persistence adapter for the real on-disk settings provider."""

    def __init__(self, config_manager: ConfigManager, overlay_manager=None):
        self.config_manager = config_manager
        self.overlay_manager = overlay_manager
        self.handles_overlay = overlay_manager is not None
        self._journal_path = self.config_manager.config_dir / ".mcp-library-save-journal.json"
        self._recover_pending()

    def commit(
        self, candidate_settings, candidate_overlay, expected_previous,
        expected_previous_overlay=None,
    ):
        journal = None
        try:
            journal = self._stage_journal(candidate_overlay)
            settings_to_save = deepcopy(candidate_settings)
            self.config_manager.save_config(settings_to_save)
            persisted = self.config_manager.load_config_strict()
            if persisted != settings_to_save:
                self.restore(expected_previous, expected_previous_overlay)
                return SaveResult(
                    False, "persistence_failure", "MCP settings were not persisted"
                )
            if candidate_overlay:
                if self.overlay_manager is None:
                    self.restore(expected_previous, expected_previous_overlay)
                    return SaveResult(
                        False, "persistence_failure", "MCP library overlay store is unavailable"
                    )
                overlay = LocalLibraryOverlay.model_validate(candidate_overlay)
                self.overlay_manager.save_overlay(overlay)
                persisted_overlay = self.overlay_manager.get_overlay(overlay.library_id)
                if persisted_overlay.model_dump(mode="json") != overlay.model_dump(mode="json"):
                    raise OSError("overlay verification failed")
            self._clear_journal(journal)
        except Exception:
            self._recover_pending()
            return SaveResult(
                False, "persistence_failure", "MCP settings or overlay could not be saved"
            )
        return SaveResult(True)

    def restore(self, snapshot, overlay_snapshot=None) -> RollbackResult:
        journal = None
        try:
            journal = self._stage_journal(
                overlay_snapshot.model_dump(mode="json")
                if isinstance(overlay_snapshot, LocalLibraryOverlay)
                else overlay_snapshot
            )
            settings_to_save = deepcopy(snapshot)
            self.config_manager.save_config(settings_to_save)
            settings_restored = self.config_manager.load_config_strict() == settings_to_save
            if not settings_restored:
                raise OSError("settings rollback verification failed")
            overlay_restored = self.overlay_manager is None or overlay_snapshot is None
            if self.overlay_manager is not None and overlay_snapshot is not None:
                previous_overlay = LocalLibraryOverlay.model_validate(overlay_snapshot)
                self.overlay_manager.save_overlay(previous_overlay)
                persisted_overlay = self.overlay_manager.get_overlay(previous_overlay.library_id)
                overlay_restored = (
                    persisted_overlay.model_dump(mode="json")
                    == previous_overlay.model_dump(mode="json")
                )
                if not overlay_restored:
                    raise OSError("overlay rollback verification failed")
            self._clear_journal(journal)
        except Exception:
            self._recover_pending()
            return RollbackResult(
                False, "rollback_failure", "Previous MCP settings and overlay could not be restored"
            )
        return RollbackResult(True)

    def _overlay_path(self, overlay: dict | None) -> Path | None:
        if not overlay or self.overlay_manager is None:
            return None
        library_id = overlay.get("library_id")
        if not library_id:
            return None
        path_method = getattr(self.overlay_manager, "_overlay_path", None)
        if callable(path_method):
            return Path(path_method(str(library_id)))
        return Path(self.overlay_manager.base_dir) / str(library_id) / "overlay.json"

    @staticmethod
    def _read_bytes(path: Path) -> bytes | None:
        try:
            return path.read_bytes() if path.is_file() else None
        except OSError:
            return None

    def _stage_journal(self, overlay: dict | None) -> dict:
        backup_dir = self.config_manager.config_dir / f".mcp-library-save-{uuid.uuid4().hex}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        settings_bytes = self._read_bytes(self.config_manager.config_path)
        overlay_path = self._overlay_path(overlay)
        overlay_bytes = self._read_bytes(overlay_path) if overlay_path else None
        if settings_bytes is not None:
            self._write_durable(backup_dir / "settings.bin", settings_bytes)
            if os.name == "posix":
                os.chmod(backup_dir / "settings.bin", 0o600)
        if overlay_bytes is not None:
            self._write_durable(backup_dir / "overlay.bin", overlay_bytes)
            if os.name == "posix":
                os.chmod(backup_dir / "overlay.bin", 0o600)
        journal = {
            "backup_dir": str(backup_dir),
            "settings_exists": settings_bytes is not None,
            "overlay_exists": overlay_bytes is not None,
            "overlay_path": str(overlay_path) if overlay_path else None,
        }
        temporary = self._journal_path.with_suffix(".tmp")
        self._write_durable(
            temporary, json.dumps(journal, separators=(",", ":")).encode("utf-8")
        )
        if os.name == "posix":
            os.chmod(backup_dir, 0o700)
            os.chmod(temporary, 0o600)
        os.replace(temporary, self._journal_path)
        self._fsync_directory(self._journal_path.parent)
        return journal

    def _recover_pending(self) -> None:
        if not self._journal_path.is_file():
            return
        try:
            journal = json.loads(self._journal_path.read_text(encoding="utf-8"))
            backup_dir = Path(journal["backup_dir"])
            self._restore_file(
                self.config_manager.config_path,
                backup_dir / "settings.bin",
                bool(journal.get("settings_exists")),
            )
            overlay_path = journal.get("overlay_path")
            if overlay_path:
                self._restore_file(
                    Path(overlay_path), backup_dir / "overlay.bin",
                    bool(journal.get("overlay_exists")),
                )
            self._clear_journal(journal)
        except Exception:
            # Leave the intent record for the next initialization; do not expose
            # serialized settings or secret values in the diagnostic.
            return

    @staticmethod
    def _restore_file(target: Path, backup: Path, existed: bool) -> None:
        if existed:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(target.suffix + ".recovery")
            ConfigManagerSettingsStore._write_durable(temporary, backup.read_bytes())
            os.replace(temporary, target)
            ConfigManagerSettingsStore._fsync_directory(target.parent)
        elif target.exists():
            target.unlink()

    @staticmethod
    def _write_durable(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(content)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        try:
            descriptor = os.open(directory, os.O_RDONLY)
        except OSError:
            return
        try:
            try:
                os.fsync(descriptor)
            except OSError:
                pass
        finally:
            os.close(descriptor)

    def _clear_journal(self, journal: dict | None) -> None:
        if self._journal_path.exists():
            self._journal_path.unlink()
            self._fsync_directory(self._journal_path.parent)
        if journal:
            shutil.rmtree(journal["backup_dir"], ignore_errors=True)


class LibraryMcpSaveTransaction:
    """Checked, no-partial-write save boundary for one library-backed row."""

    def __init__(
        self,
        *,
        store: CheckedSettingsStore,
        previous: Any,
        candidate: Any,
        overlay: dict,
        registry=None,
        registry_snapshot=None,
        overlay_manager=None,
        overlay_snapshot=None,
        metrics: MetricsTrackerProtocol | None = None,
    ):
        self.store = store
        self.previous = deepcopy(previous)
        self.candidate = deepcopy(candidate)
        self.overlay = deepcopy(overlay)
        self.registry = registry
        self.registry_snapshot = deepcopy(registry_snapshot)
        self.overlay_manager = overlay_manager
        if isinstance(overlay_snapshot, LocalLibraryOverlay):
            self.overlay_snapshot = overlay_snapshot.model_dump(mode="json")
        else:
            self.overlay_snapshot = deepcopy(overlay_snapshot)
        self._metrics = resolve_metrics(metrics)

    def commit(self) -> SaveResult:
        started_at = time.perf_counter()
        result = self.store.commit(
            self.candidate,
            self.overlay,
            self.previous,
            expected_previous_overlay=self.overlay_snapshot,
        )
        if not result.committed:
            self._metrics.track_mcp_library_save(
                result.category or "persistence_failure",
                time.perf_counter() - started_at,
            )
            logger.warning(
                "mcp_library_save_failed outcome=%s",
                result.category or "persistence_failure",
            )
            return result
        if self.overlay_manager is not None and self.overlay and not getattr(
            self.store, "handles_overlay", False
        ):
            try:
                overlay = LocalLibraryOverlay.model_validate(self.overlay)
                self.overlay_manager.save_overlay(overlay)
                if hasattr(self.overlay_manager, "get_overlay"):
                    persisted = self.overlay_manager.get_overlay(overlay.library_id)
                    if persisted.model_dump(mode="json") != overlay.model_dump(mode="json"):
                        raise ValueError("overlay verification failed")
            except Exception:
                self.rollback()
                return SaveResult(
                    False, "persistence_failure", "MCP library overlay could not be saved"
                )
        self._metrics.track_mcp_library_save(
            "commit", time.perf_counter() - started_at
        )
        logger.info("mcp_library_save_committed")
        return result

    def rollback(self) -> RollbackResult:
        started_at = time.perf_counter()
        result = self.store.restore(self.previous, self.overlay_snapshot)
        try:
            if (
                self.overlay_manager is not None
                and self.overlay_snapshot is not None
                and not getattr(self.store, "handles_overlay", False)
            ):
                previous_overlay = LocalLibraryOverlay.model_validate(self.overlay_snapshot)
                self.overlay_manager.save_overlay(previous_overlay)
                if hasattr(self.overlay_manager, "get_overlay"):
                    persisted = self.overlay_manager.get_overlay(previous_overlay.library_id)
                    if (
                        persisted.model_dump(mode="json")
                        != previous_overlay.model_dump(mode="json")
                    ):
                        raise ValueError("overlay rollback verification failed")
            if self.registry is not None and self.registry_snapshot is not None:
                self.registry.restore_snapshot(self.registry_snapshot)
        except Exception:
            self._metrics.track_mcp_library_save(
                "rollback_failure", time.perf_counter() - started_at
            )
            logger.warning("mcp_library_save_rollback_failed", exc_info=True)
            return RollbackResult(
                False, "rollback_failure", "MCP library state could not be restored"
            )
        self._metrics.track_mcp_library_save(
            "rollback", time.perf_counter() - started_at
        )
        logger.warning("mcp_library_save_rolled_back")
        return result


class McpServerSettingsController:
    """Owns MCP composition, persisted endpoint rows, and per-instance lifecycle.

    ``settings_provider`` is a callable rather than a stored value because the composition
    root replaces its ``AppSettings`` instance whenever the settings dialog commits.
    """
    def __init__(
        self,
        *,
        settings_provider: Callable[[], AppSettings] | None = None,
        config_manager: ConfigManager | None = None,
        collection_lookup: Callable[[str], Collection | None] | None = None,
        environment_lookup: Callable[[str], Environment | None] | None = None,
        metrics: MetricsTrackerProtocol | None = None,
        template_service: TemplateService | None = None,
        mcp_manager: MCPServerManager | None = None,
        registry: MCPServerRegistry | None = None,
        library_service=None,
    ) -> None:
        if library_service is None:
            from pypost.core.library_manager_service import LibraryManagerService

            library_service = LibraryManagerService()
        self._config_manager = config_manager
        self._metrics = resolve_metrics(metrics)
        self._standalone_settings = (
            config_manager.load_config()
            if config_manager is not None and hasattr(config_manager, "load_config")
            else AppSettings()
        )
        self._settings_provider = settings_provider or (lambda: self._standalone_settings)
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
            if getattr(self.registry, "library_service", None) is None:
                self.registry.library_service = library_service
            if environment_lookup is not None:
                self.registry._environment_lookup = environment_lookup
        else:
            logger.debug("mcp_registry_source source=new")
            self.registry = MCPServerRegistry(
                collection_lookup=collection_lookup or (lambda _id: None),
                environment_lookup=environment_lookup or (lambda _id: None),
                metrics=metrics,
                template_service=template_service,
                library_service=library_service,
            )
        self.registry.reconfiguration_finished.connect(
            self._on_mcp_server_reconfiguration_finished
        )
        self._load_persisted_mcp_servers()

    def save_library_server(self, configuration, selection, handoff) -> None:
        """Validate and install a library row while preserving stable identity."""
        from pypost.core.library_runtime_resolver import LibraryRuntimeResolver

        resolver = LibraryRuntimeResolver(
            library_service=self.registry.library_service,
            environment_lookup=getattr(self.registry, "_environment_lookup", None),
            metrics=self._metrics,
        )
        overlay_manager = getattr(self.registry.library_service, "overlay_manager", None)
        library_id = str(selection.get("library_id") or "")
        overlay_snapshot = (
            overlay_manager.get_overlay(library_id)
            if overlay_manager is not None and library_id
            else None
        )
        overlay_candidate = self._overlay_candidate(
            handoff, overlay_snapshot, library_id
        )
        candidate_overlay = LocalLibraryOverlay.model_validate(overlay_candidate)
        resolver.resolve(
            selection, configuration.environment_id, candidate_overlay=candidate_overlay
        )
        configuration = configuration.model_copy(
            update={
                "library_id": selection["library_id"],
                "manifest_id": selection["manifest_id"],
                "library_collection_path": selection["path"],
                "library_collection_index": selection.get("index"),
            }
        )
        previous_settings = deepcopy(self._settings)
        previous_registry = self.registry.snapshot()
        current = {
            item.id: item.model_copy(deep=True) for item in self._settings.mcp_servers
        }
        current[configuration.id] = configuration.model_copy(deep=True)
        candidate = previous_settings.model_copy(update={"mcp_servers": list(current.values())})
        store = self._checked_store(overlay_manager=overlay_manager)
        transaction = LibraryMcpSaveTransaction(
            store=store, previous=previous_settings, candidate=candidate,
            overlay=overlay_candidate,
            registry=self.registry, registry_snapshot=previous_registry,
            overlay_manager=overlay_manager, overlay_snapshot=overlay_snapshot,
            metrics=self._metrics,
        )
        self.registry.validate_library_candidate(
            configuration, candidate_overlay=candidate_overlay
        )
        result = transaction.commit()
        if not result.committed:
            raise ValueError(f"{result.category}: {result.safe_message}")
        try:
            self.registry.install_library_candidate(
                configuration, candidate_overlay=candidate_overlay
            )
        except Exception as error:
            rollback = transaction.rollback()
            if not rollback.restored:
                raise RuntimeError(rollback.safe_message) from error
            self.registry.restore_snapshot(previous_registry)
            raise
        self._settings.mcp_servers = list(current.values())

    @staticmethod
    def _overlay_candidate(handoff, current, library_id: str) -> dict[str, Any]:
        """Turn picker handoff data into a complete persisted overlay snapshot."""
        base = current.model_dump(mode="json") if isinstance(current, LocalLibraryOverlay) else {}
        payload = handoff
        if isinstance(handoff, dict) and isinstance(handoff.get("overlay"), dict):
            payload = handoff["overlay"]
        elif hasattr(handoff, "overlay"):
            payload = getattr(handoff, "overlay")
        if isinstance(payload, LocalLibraryOverlay):
            payload = payload.model_dump(mode="json")
        if isinstance(payload, dict) and any(
            key in payload for key in ("active_profile", "secrets", "overrides")
        ):
            base.update(deepcopy(payload))
        base["library_id"] = library_id
        return LocalLibraryOverlay.model_validate(base).model_dump(mode="json")

    def reload_mcp_servers(self) -> list[McpServerConfiguration]:
        if self._config_manager is not None and hasattr(self._config_manager, "load_config_strict"):
            loaded = self._config_manager.load_config_strict()
            self._settings.mcp_servers = loaded.mcp_servers
            self.registry.clear()
            self._load_persisted_mcp_servers()
        return self.mcp_server_configurations()

    def _checked_store(self, *, overlay_manager=None):
        if self._config_manager is not None and hasattr(self._config_manager, "load_config_strict"):
            return ConfigManagerSettingsStore(self._config_manager, overlay_manager)
        return CheckedSettingsStore()

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
        if configuration.library_id:
            selection = configuration.library_selection
            if selection is None:
                raise ValueError("library_invalid: library identity is incomplete")
            from pypost.core.library_runtime_resolver import LibraryRuntimeResolver
            handoff = LibraryRuntimeResolver(
                library_service=self.registry.library_service,
                environment_lookup=getattr(self.registry, "_environment_lookup", None),
            ).resolve(selection, configuration.environment_id)
            self.save_library_server(configuration, selection, handoff)
            return
        try:
            previous = self._mcp_server_configuration(configuration.id)
        except KeyError:
            previous = None
        if previous is not None and self.registry.is_running(configuration.id):
            # A running row must use the registry's transactional replacement
            # path; merely persisting it would leave the old endpoint live.
            self.registry.reconfigure(configuration.id, configuration)
            return
        reason = "update" if previous is not None else "create"
        previous_settings = deepcopy(self._settings)
        previous_registry = self.registry.snapshot()
        configurations = {
            existing.id: existing.model_copy(deep=True)
            for existing in self._settings.mcp_servers
        }
        configurations[configuration.id] = configuration.model_copy(deep=True)
        candidate = previous_settings.model_copy(
            update={"mcp_servers": list(configurations.values())}
        )
        store = self._checked_store()
        result = LibraryMcpSaveTransaction(
            store=store, previous=previous_settings, candidate=candidate, overlay={}
        ).commit()
        if not result.committed:
            raise ValueError(f"{result.category}: {result.safe_message}")
        try:
            self.registry.upsert(configuration)
        except Exception:
            store.restore(previous_settings)
            self.registry.restore_snapshot(previous_registry)
            raise
        self._settings.mcp_servers = list(configurations.values())
        if not isinstance(store, ConfigManagerSettingsStore):
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
        if self._config_manager is not None:
            self._config_manager.save_config(self._settings)
