"""Repro tests for collection-scoped variables and catalog manifest (PYPOST-1409).

Asserts target contract before Step 4 implementation:
1. Pure catalog manifest instantiation (variables/presets omitted).
2. Legacy manifest warning and migration on ingestion.
3. Collection variable authority over legacy manifest variables in resolution engine.
4. 3-tier precedence hierarchy (defaults -> presets -> overlay overrides/secrets).
5. Elimination of cross-collection namespace pollution.
"""

from __future__ import annotations

import pytest

from pypost.core.library_manifest import (
    deserialize_manifest_from_yaml,
    serialize_manifest_to_dict,
)
from pypost.core.variable_resolver import LibraryVariableResolver
from pypost.models.collection_variable import CollectionVariable
from pypost.models.library_manifest import (
    LibraryManifest,
    LocalLibraryOverlay,
    VariableProvenance,
)
from pypost.models.models import Collection

pytestmark = pytest.mark.timeout(30)


@pytest.mark.timeout(30)
def test_catalog_manifest_instantiation_without_variables():
    """Verify that a LibraryManifest can be instantiated cleanly as a pure catalog index
    without requiring library-level variables or presets.
    """
    manifest = LibraryManifest(
        id="lib-catalog-1",
        name="Catalog Only",
        description="Pure catalog index of API collections without variables or presets.",
        collections=["collections/auth.json", "collections/users.json"],
    )

    assert manifest.id == "lib-catalog-1"
    assert manifest.name == "Catalog Only"
    assert manifest.collections == ["collections/auth.json", "collections/users.json"]
    assert manifest.variables == []
    assert manifest.presets == {}

    # Serialization should succeed and preserve catalog index metadata
    data = serialize_manifest_to_dict(manifest)
    assert data["id"] == "lib-catalog-1"
    assert data["name"] == "Catalog Only"
    assert data["collections"] == ["collections/auth.json", "collections/users.json"]


@pytest.mark.timeout(30)
def test_legacy_manifest_ingestion_emits_deprecation_warning():
    """Verify that deserializing a legacy manifest containing top-level variables and presets
    emits a DeprecationWarning while preserving backward compatibility.
    """
    legacy_yaml = (
        "id: lib-legacy-1\n"
        "name: Legacy Variable Library\n"
        "version: 1.0.0\n"
        "description: Library containing legacy root variables and presets\n"
        "collections:\n"
        "  - collections/sample.json\n"
        "variables:\n"
        "  - name: api_key\n"
        "    type: string\n"
        "    default: secret-123\n"
        "    description: Legacy key\n"
        "presets:\n"
        "  prod:\n"
        "    api_key: prod-key-456\n"
    )

    with pytest.warns(DeprecationWarning, match=r"(?i)deprecated"):
        manifest = deserialize_manifest_from_yaml(legacy_yaml)

    assert manifest.id == "lib-legacy-1"
    assert len(manifest.variables) == 1
    assert manifest.variables[0].name == "api_key"
    assert "prod" in manifest.presets
    assert manifest.presets["prod"]["api_key"] == "prod-key-456"


@pytest.mark.timeout(30)
def test_collection_variable_authority_over_legacy_manifest():
    """Verify that collection-defined variables and presets take precedence over legacy
    manifest declarations when resolved by LibraryVariableResolver.
    """
    # Collection defines its own authoritative default and profile preset
    collection = Collection(
        id="col-billing",
        name="Billing Collection",
        variables=[
            CollectionVariable(
                name="api_url",
                type="string",
                default="https://collection.default.com",
                description="Collection default URL",
            ),
            CollectionVariable(
                name="col_only_param",
                type="string",
                default="col_exclusive",
                description="Only in collection",
            ),
        ],
        presets={
            "prod": {
                "api_url": "https://collection.prod.com",
            },
        },
    )

    # Legacy manifest contains conflicting definitions for api_url, plus fallback-only variables
    legacy_manifest = LibraryManifest(
        id="lib-legacy-conflict",
        name="Conflicting Legacy Library",
        collections=["collections/billing.json"],
        variables=[
            CollectionVariable(
                name="api_url",
                type="string",
                default="https://legacy.manifest.com",
                description="Legacy manifest conflicting URL",
            ),
            CollectionVariable(
                name="legacy_fallback_var",
                type="string",
                default="https://fallback.legacy.com",
                description="Legacy-only variable",
            ),
        ],
        presets={
            "prod": {
                "api_url": "https://legacy.prod.com",
                "legacy_fallback_preset_var": "legacy_preset_value",
            },
        },
    )

    resolver = LibraryVariableResolver()

    # 1. Active profile resolution: Collection preset MUST take authority over manifest preset
    result_prod = resolver.resolve(
        manifest=legacy_manifest,
        collection=collection,
        active_profile="prod",
    )
    assert result_prod.variables["api_url"] == "https://collection.prod.com"
    assert result_prod.provenance["api_url"] == VariableProvenance.PROFILE
    # Fallback keys from legacy manifest are retained if not declared in collection
    assert result_prod.variables["legacy_fallback_var"] == "https://fallback.legacy.com"
    assert (
        result_prod.variables["legacy_fallback_preset_var"] == "legacy_preset_value"
    )

    # 2. Base default resolution (no profile): Collection default MUST take authority
    result_base = resolver.resolve(
        manifest=legacy_manifest,
        collection=collection,
        active_profile=None,
    )
    assert result_base.variables["api_url"] == "https://collection.default.com"
    assert result_base.provenance["api_url"] == VariableProvenance.DEFAULT
    assert result_base.variables["col_only_param"] == "col_exclusive"
    assert result_base.variables["legacy_fallback_var"] == "https://fallback.legacy.com"


@pytest.mark.timeout(30)
def test_three_tier_resolution_with_local_overlay():
    """Verify the 3-tier precedence hierarchy:
    Tier 1 (Base defaults from Collection) ->
    Tier 2 (Profile presets from Collection) ->
    Tier 3 (Local overlay overrides and secrets).
    """
    collection = Collection(
        id="col-payments",
        name="Payments",
        variables=[
            CollectionVariable(
                name="api_endpoint",
                type="string",
                default="https://api.default.example.com",
                description="Default endpoint",
            ),
            CollectionVariable(
                name="timeout",
                type="integer",
                default=10,
                description="Timeout in seconds",
            ),
            CollectionVariable(
                name="api_secret",
                type="string",
                default=None,
                secret=True,
                required=True,
                description="Secret token",
            ),
            CollectionVariable(
                name="base_currency",
                type="string",
                default="USD",
                description="Base currency",
            ),
        ],
        presets={
            "staging": {
                "api_endpoint": "https://staging.api.example.com",
                "timeout": 30,
            },
            "prod": {
                "api_endpoint": "https://prod.api.example.com",
                "timeout": 15,
            },
        },
    )

    manifest = LibraryManifest(
        id="lib-pure-catalog",
        name="Pure Catalog Library",
        collections=["collections/payments.json"],
    )

    overlay = LocalLibraryOverlay(
        library_id="lib-pure-catalog",
        active_profile="staging",
        overrides={
            "timeout": 60,
        },
        secrets={
            "api_secret": "local-super-secret-token",
        },
    )

    resolver = LibraryVariableResolver()

    # Tier 1 alone (no profile, no overlay): defaults only
    res_tier1 = resolver.resolve(
        manifest=manifest,
        collection=collection,
        active_profile=None,
        overlay=None,
    )
    assert res_tier1.variables["api_endpoint"] == "https://api.default.example.com"
    assert res_tier1.provenance["api_endpoint"] == VariableProvenance.DEFAULT
    assert res_tier1.variables["timeout"] == 10
    assert res_tier1.provenance["timeout"] == VariableProvenance.DEFAULT
    assert res_tier1.variables["base_currency"] == "USD"
    assert res_tier1.provenance["base_currency"] == VariableProvenance.DEFAULT

    # Tier 2 (active profile "staging", no overlay): profile overrides default
    res_tier2 = resolver.resolve(
        manifest=manifest,
        collection=collection,
        active_profile="staging",
        overlay=None,
    )
    assert res_tier2.variables["api_endpoint"] == "https://staging.api.example.com"
    assert res_tier2.provenance["api_endpoint"] == VariableProvenance.PROFILE
    assert res_tier2.variables["timeout"] == 30
    assert res_tier2.provenance["timeout"] == VariableProvenance.PROFILE
    assert res_tier2.variables["base_currency"] == "USD"
    assert res_tier2.provenance["base_currency"] == VariableProvenance.DEFAULT

    # Tier 3 (overlay applied): local overrides and secrets take highest priority
    res_tier3 = resolver.resolve(
        manifest=manifest,
        collection=collection,
        active_profile=None,
        overlay=overlay,
    )
    # Overlay active_profile is "staging" -> endpoint comes from staging preset
    assert res_tier3.variables["api_endpoint"] == "https://staging.api.example.com"
    assert res_tier3.provenance["api_endpoint"] == VariableProvenance.PROFILE
    # Timeout is overridden by local overlay override
    assert res_tier3.variables["timeout"] == 60
    assert res_tier3.provenance["timeout"] == VariableProvenance.LOCAL_OVERRIDE
    # Secret is supplied by local overlay secrets
    assert res_tier3.variables["api_secret"] == "local-super-secret-token"
    assert res_tier3.provenance["api_secret"] == VariableProvenance.LOCAL_SECRET
    # Base currency falls back through tiers to Tier 1 default
    assert res_tier3.variables["base_currency"] == "USD"
    assert res_tier3.provenance["base_currency"] == VariableProvenance.DEFAULT


@pytest.mark.timeout(30)
def test_elimination_of_cross_collection_namespace_pollution():
    """Verify that resolving variables for a specific collection does not suffer from
    namespace pollution by variables or presets belonging to other collections.
    """
    col_jira = Collection(
        id="col-jira",
        name="Jira Collection",
        variables=[
            CollectionVariable(
                name="jira_token",
                type="string",
                default="jira-default-token",
                description="Jira token",
            ),
        ],
        presets={
            "prod": {
                "jira_token": "jira-prod-token",
            },
        },
    )

    col_github = Collection(
        id="col-github",
        name="GitHub Collection",
        variables=[
            CollectionVariable(
                name="github_pat",
                type="string",
                default="ghp_default_token",
                description="GitHub token",
            ),
        ],
        presets={
            "prod": {
                "github_pat": "ghp_prod_token",
            },
        },
    )

    # Legacy manifest declared ambient variables and presets belonging to other collections
    manifest = LibraryManifest(
        id="lib-multi-coll",
        name="Multi Collection Tools",
        collections=["collections/jira.json", "collections/github.json"],
        variables=[
            CollectionVariable(
                name="github_pat",
                type="string",
                default="ghp_ambient_leak",
                description="Leaked GitHub variable declared at library root",
            ),
        ],
        presets={
            "prod": {
                "github_pat": "ghp_ambient_prod_leak",
                "github.pat": "ghp_namespaced_leak",
            },
        },
    )

    resolver = LibraryVariableResolver()

    # When resolving col_jira, GitHub-specific variables must not contaminate the resolved scope
    result_jira = resolver.resolve(
        manifest=manifest,
        collection=col_jira,
        active_profile="prod",
    )

    assert "jira_token" in result_jira.variables
    assert result_jira.variables["jira_token"] == "jira-prod-token"
    assert "github_pat" not in result_jira.variables
    assert "github.pat" not in result_jira.variables

    # Symmetrically, resolving col_github must not be contaminated by Jira variables
    result_github = resolver.resolve(
        manifest=manifest,
        collection=col_github,
        active_profile="prod",
    )

    assert "github_pat" in result_github.variables
    assert "jira_token" not in result_github.variables
