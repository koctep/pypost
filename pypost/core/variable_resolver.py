"""3-tier effective variable resolution engine (PYPOST-1221).

Resolves effective runtime variables following the precedence hierarchy:
Layer 1: Manifest & Collection Defaults
Layer 2: Active Preset Profile
Layer 3: Local Overlay Secrets and Overrides

Performs type validation and required variable / secret checks with provenance tracking.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from pypost.models.collection_variable import (
    CollectionVariable,
    validate_variable_value,
)
from pypost.models.library_manifest import (
    LibraryManifest,
    LocalLibraryOverlay,
    ManifestDiagnosticError,
    ResolvedVariable,
    VariableProvenance,
    VariableResolutionContext,
    VariableResolutionResult,
)
from pypost.models.models import Collection

logger = logging.getLogger(__name__)

__all__ = [
    "LibraryVariableResolver",
    "resolve_detailed_variables",
    "resolve_effective_variables",
]


class LibraryVariableResolver:
    """Evaluates effective variables across manifest, profile, and local overlay layers."""

    def resolve(
        self,
        manifest: Optional[LibraryManifest] = None,
        overlay: Optional[LocalLibraryOverlay] = None,
        active_profile: Optional[str] = None,
        collection: Optional[Collection] = None,
        strict_required: bool = False,
    ) -> VariableResolutionResult:
        """Resolve effective variables following the 3-tier precedence hierarchy.

        Args:
            manifest: The library manifest descriptor.
            overlay: Local user overlay containing secrets and overrides.
            active_profile: Name of active preset profile (overrides overlay.active_profile).
            collection: Optional single collection instance for collection-level defaults.
            strict_required: If True, raises ManifestDiagnosticError for missing
                required variables.

        Returns:
            VariableResolutionResult: Effective variables, provenance, and diagnostic status.
        """
        variables: Dict[str, Any] = {}
        provenance: Dict[str, VariableProvenance] = {}
        schemas: Dict[str, CollectionVariable] = {}

        # ---------------------------------------------------------------------
        # Collect Variable Schemas
        # ---------------------------------------------------------------------
        if collection and hasattr(collection, "variables") and collection.variables:
            for var in collection.variables:
                schemas[var.name] = var

        if manifest and manifest.variables:
            for var in manifest.variables:
                schemas[var.name] = var

        # ---------------------------------------------------------------------
        # Layer 1 (Base Defaults): Collection then Manifest Defaults
        # ---------------------------------------------------------------------
        if collection and hasattr(collection, "variables") and collection.variables:
            for var in collection.variables:
                if var.default is not None:
                    variables[var.name] = var.default
                    provenance[var.name] = VariableProvenance.DEFAULT

        if manifest and manifest.variables:
            for var in manifest.variables:
                if var.default is not None:
                    variables[var.name] = var.default
                    provenance[var.name] = VariableProvenance.DEFAULT

        # ---------------------------------------------------------------------
        # Layer 2 (Active Preset Profile)
        # ---------------------------------------------------------------------
        profile_name = (
            active_profile
            if active_profile is not None
            else (overlay.active_profile if overlay else None)
        )

        if profile_name:
            if manifest and manifest.presets and profile_name in manifest.presets:
                profile_vars = manifest.presets[profile_name]
                if isinstance(profile_vars, dict):
                    for k, v in profile_vars.items():
                        variables[k] = v
                        provenance[k] = VariableProvenance.PROFILE

            if collection and hasattr(collection, "presets") and collection.presets:
                if profile_name in collection.presets:
                    col_preset_vars = collection.presets[profile_name]
                    if isinstance(col_preset_vars, dict):
                        for k, v in col_preset_vars.items():
                            if (
                                not manifest
                                or not manifest.presets
                                or profile_name not in manifest.presets
                                or k not in manifest.presets[profile_name]
                            ):
                                variables[k] = v
                                provenance[k] = VariableProvenance.PROFILE

        # ---------------------------------------------------------------------
        # Layer 3 (Local Overlay: Overrides & Secrets)
        # ---------------------------------------------------------------------
        if overlay:
            if overlay.overrides:
                for k, v in overlay.overrides.items():
                    variables[k] = v
                    provenance[k] = VariableProvenance.LOCAL_OVERRIDE

            if overlay.secrets:
                for k, v in overlay.secrets.items():
                    variables[k] = v
                    provenance[k] = VariableProvenance.LOCAL_SECRET

        # ---------------------------------------------------------------------
        # Schema Validation & Required Variable Checks
        # ---------------------------------------------------------------------
        errors: list[str] = []
        missing_required: list[str] = []

        for name, schema in schemas.items():
            if name in variables:
                val = variables[name]
                if val is not None and not validate_variable_value(val, schema.type):
                    val_repr = "[REDACTED]" if schema.secret else repr(val)
                    errors.append(
                        f"Variable '{name}' value {val_repr} is not of expected "
                        f"type '{schema.type}'"
                    )

            if schema.required:
                val = variables.get(name)
                if val is None or val == "":
                    missing_required.append(name)

        default_count = sum(
            1 for p in provenance.values() if p == VariableProvenance.DEFAULT
        )
        profile_count = sum(
            1 for p in provenance.values() if p == VariableProvenance.PROFILE
        )
        override_count = sum(
            1 for p in provenance.values() if p == VariableProvenance.LOCAL_OVERRIDE
        )
        secret_count = sum(
            1 for p in provenance.values() if p == VariableProvenance.LOCAL_SECRET
        )

        logger.debug(
            "variable_resolution_completed total_resolved=%d default_count=%d "
            "profile_count=%d override_count=%d secret_count=%d "
            "missing_required_count=%d error_count=%d",
            len(variables),
            default_count,
            profile_count,
            override_count,
            secret_count,
            len(missing_required),
            len(errors),
        )

        if missing_required:
            logger.warning(
                "variable_resolution_missing_required missing_count=%d missing_names=%s",
                len(missing_required),
                missing_required,
            )

        if errors:
            logger.warning(
                "variable_resolution_validation_failed error_count=%d errors=%s",
                len(errors),
                errors,
            )

        result = VariableResolutionResult(
            variables=variables,
            provenance=provenance,
            missing_required=missing_required,
            errors=errors,
        )

        if strict_required:
            if missing_required:
                raise ManifestDiagnosticError(
                    code="MISSING_REQUIRED_SECRET",
                    message=f"Missing required variables or secrets: {', '.join(missing_required)}",
                    details={"missing_required": missing_required},
                )
            if errors:
                raise ManifestDiagnosticError(
                    code="TYPE_MISMATCH",
                    message=f"Variable validation failed: {'; '.join(errors)}",
                    details={"errors": errors},
                )

        return result

    def resolve_context(
        self, context: VariableResolutionContext
    ) -> VariableResolutionResult:
        """Resolve effective variables from a VariableResolutionContext object."""
        return self.resolve(
            manifest=context.manifest,
            overlay=context.overlay,
            active_profile=context.active_profile,
            collection=context.collection,
            strict_required=context.strict_required,
        )


def resolve_effective_variables(
    collection: Optional[Collection] = None,
    manifest: Optional[LibraryManifest] = None,
    active_profile: Optional[str] = None,
    overlay: Optional[LocalLibraryOverlay] = None,
) -> dict[str, Any]:
    """Resolve flat effective variable dictionary for request execution."""
    resolver = LibraryVariableResolver()
    result = resolver.resolve(
        manifest=manifest,
        overlay=overlay,
        active_profile=active_profile,
        collection=collection,
        strict_required=False,
    )
    return result.variables


def resolve_detailed_variables(
    collection: Optional[Collection] = None,
    manifest: Optional[LibraryManifest] = None,
    active_profile: Optional[str] = None,
    overlay: Optional[LocalLibraryOverlay] = None,
) -> dict[str, ResolvedVariable]:
    """Resolve detailed ResolvedVariable objects with origins and secret metadata."""
    resolver = LibraryVariableResolver()
    result = resolver.resolve(
        manifest=manifest,
        overlay=overlay,
        active_profile=active_profile,
        collection=collection,
        strict_required=False,
    )

    secret_keys: set[str] = set()
    if manifest and manifest.variables:
        for var in manifest.variables:
            if var.secret:
                secret_keys.add(var.name)
    if collection and hasattr(collection, "variables") and collection.variables:
        for var in collection.variables:
            if var.secret:
                secret_keys.add(var.name)
    if overlay and overlay.secrets:
        secret_keys.update(overlay.secrets.keys())

    detailed: dict[str, ResolvedVariable] = {}
    for name, value in result.variables.items():
        origin = result.provenance.get(name, VariableProvenance.DEFAULT)
        detailed[name] = ResolvedVariable(
            name=name,
            value=value,
            origin=origin,
            is_secret=(name in secret_keys or origin == VariableProvenance.LOCAL_SECRET),
        )

    logger.debug(
        "variable_resolution_detailed_completed total=%d secrets_count=%d",
        len(detailed),
        sum(1 for v in detailed.values() if v.is_secret),
    )

    return detailed
