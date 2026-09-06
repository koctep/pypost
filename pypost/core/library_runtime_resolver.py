"""Pure preparation and validation boundary for library-backed MCP rows."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import logging
import time
from typing import Any

from pypost.core.collection_serializer import read_collection_file
from pypost.core.library_manifest import find_and_read_manifest, validate_manifest_collections
from pypost.models.collection_variable import validate_variable_value
from pypost.core.variable_resolver import LibraryVariableResolver
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EnvironmentDraft:
    values: dict[str, Any]
    provenance: dict[str, str]
    safe_diagnostics: str = ""


@dataclass(frozen=True)
class RuntimeInputs:
    selection: dict[str, Any]
    environment_id: str
    environment: dict[str, Any]
    collection_requests: list[Any]
    hidden_keys: set[str]


class LibraryRuntimeResolver:
    """Resolve stable library identities and local environment layers."""

    def __init__(self, *, library_service=None, environment_lookup=None, metrics=None):
        self.library_service = library_service
        self.environment_lookup = environment_lookup or (lambda _id: None)
        self._metrics: MetricsTrackerProtocol = resolve_metrics(metrics)

    def resolve(
        self,
        selection: dict[str, Any],
        environment_id: str,
        candidate_overlay=None,
    ) -> RuntimeInputs:
        started_at = time.monotonic()
        logger.info(
            "mcp_library_runtime_validation_started library_id=%s manifest_id=%s",
            selection.get("library_id", "unknown"), selection.get("manifest_id", "unknown"),
        )
        try:
            result = self._resolve(selection, environment_id, candidate_overlay)
        except ValueError as error:
            category = str(error).split(":", 1)[0]
            self._metrics.track_mcp_library_validation(category)
            logger.warning(
                "mcp_library_runtime_validation_failed category=%s duration_seconds=%.3f",
                category, time.monotonic() - started_at,
            )
            raise
        self._metrics.track_mcp_library_validation("success")
        logger.info(
            "mcp_library_runtime_validation_completed duration_seconds=%.3f "
            "request_count=%d variable_count=%d",
            time.monotonic() - started_at, len(result.collection_requests), len(result.environment),
        )
        return result

    def _resolve(
        self, selection: dict[str, Any], environment_id: str, candidate_overlay=None
    ) -> RuntimeInputs:
        self.validate_selection(selection, profile_id=environment_id)
        service = self.library_service
        if service is None:
            raise ValueError("library_invalid: connected library service is unavailable")
        get_connection = getattr(service, "get_connection", None)
        record = get_connection(selection["library_id"]) if callable(get_connection) else None
        if record is None:
            raise ValueError("library_invalid: selected library is no longer connected")
        path_method = getattr(service, "resolve_path", None)
        root = path_method(record) if callable(path_method) else getattr(record, "local_path", None)
        if root is None:
            raise ValueError("library_invalid: connected library has no local path")
        try:
            manifest, _ = find_and_read_manifest(root)
        except Exception as error:
            raise ValueError("manifest_invalid: selected library manifest is unreadable") from error
        if manifest.id != selection["manifest_id"]:
            raise ValueError("manifest_invalid: selected manifest no longer matches the library")
        if validate_manifest_collections(manifest, manifest_dir=root):
            raise ValueError("collection_missing: selected library collection is unavailable")
        relative = str(selection["path"])
        if relative not in manifest.collections:
            raise ValueError(
                "collection_missing: selected collection is not declared by the manifest"
            )
        try:
            collection = read_collection_file(root / relative)
        except Exception as error:
            raise ValueError("collection_missing: selected collection could not be read") from error
        requests = [deepcopy(request) for request in collection.requests]
        overlay_manager = getattr(service, "overlay_manager", None)
        overlay = candidate_overlay
        if overlay is None and overlay_manager is not None:
            overlay = overlay_manager.get_overlay(selection["library_id"])
        environment = self.environment_lookup(environment_id) if environment_id else None
        active_profile = getattr(overlay, "active_profile", None)
        collection_profiles = getattr(collection, "presets", {}) or {}
        available_profiles = set(manifest.presets) | set(collection_profiles)
        if active_profile and active_profile not in available_profiles:
            raise ValueError("profile_missing: selected library profile is unavailable")

        if active_profile:
            profile_id = active_profile
            # A collection may define a profile that is not present in the
            # library manifest.  Keep manifest values authoritative when both
            # layers define the same key, while still making collection-only
            # profiles available to the resolver.
            profile = dict(manifest.presets.get(active_profile, {}))
            for name, value in collection_profiles.get(active_profile, {}).items():
                profile.setdefault(name, value)
        elif environment is not None:
            # An MCP row selects a workspace Environment by ID.  Library preset
            # names are optional and must not be confused with that identity.
            profile_id = environment_id
            profile = dict(environment.variables)
        elif environment_id in available_profiles:
            profile_id = environment_id
            profile = dict(manifest.presets.get(environment_id, {}))
            profile.update(collection_profiles.get(environment_id, {}))
        else:
            raise ValueError("profile_missing: selected profile is unavailable")

        if environment is not None and active_profile:
            profile = dict(environment.variables)
            profile.update(manifest.presets.get(active_profile, {}))
            for name, value in collection_profiles.get(active_profile, {}).items():
                profile.setdefault(name, value)
        if profile_id not in manifest.presets:
            manifest = manifest.model_copy(
                update={"presets": {**manifest.presets, profile_id: profile}}
            )
        resolved = LibraryVariableResolver().resolve(
            manifest=manifest, overlay=overlay, active_profile=profile_id,
            collection=collection, strict_required=False,
        )
        if resolved.missing_required:
            raise ValueError("profile_invalid: required library variables are missing")
        if resolved.errors:
            raise ValueError("profile_invalid: library variables are invalid")
        hidden_keys = {
            variable.name for variable in manifest.variables if variable.secret
        }
        hidden_keys |= {
            variable.name for variable in collection.variables if variable.secret
        }
        hidden_keys |= set(getattr(overlay, "secrets", {}).keys())
        if environment is not None:
            hidden_keys |= set(environment.hidden_keys)
        return RuntimeInputs(
            deepcopy(selection), profile_id, resolved.variables, requests, hidden_keys
        )

    def validate_selection(self, selection: dict[str, Any], profile_id: str) -> None:
        if not selection.get("library_id"):
            raise ValueError("library_invalid: library identity is missing")
        if not selection.get("manifest_id") or not selection.get("path"):
            raise ValueError("manifest_invalid: manifest identity is incomplete")

    def prepare_environment(
        self,
        *,
        defaults: dict[str, Any],
        profile: dict[str, Any],
        overrides: dict[str, Any],
        secrets: dict[str, Any],
        declarations: dict[str, dict[str, Any]],
    ) -> EnvironmentDraft:
        values: dict[str, Any] = {}
        provenance: dict[str, str] = {}
        for source, layer in (("default", defaults), ("profile", profile),
                              ("override", overrides), ("secret", secrets)):
            for name, value in layer.items():
                values[name] = deepcopy(value)
                provenance[name] = source
        errors: list[str] = []
        for name, declaration in declarations.items():
            value = values.get(name)
            if declaration.get("required") and (value is None or value == ""):
                errors.append(f"required variable missing: {name}")
            expected = str(declaration.get("type") or "")
            if value is not None and not validate_variable_value(value, expected):
                errors.append(f"type mismatch for variable: {name}")
        if errors:
            raise ValueError("; ".join(errors))
        safe = ", ".join(f"{name}={source}" for name, source in provenance.items())
        return EnvironmentDraft(values, provenance, safe)
