"""Tests for collection namespace variable resolution in shared libraries (PYPOST-1227)."""
from __future__ import annotations

import pytest

from pypost.core.variable_resolver import LibraryVariableResolver
from pypost.models.collection_variable import CollectionVariable
from pypost.models.library_manifest import (
    LibraryManifest,
    LocalLibraryOverlay,
    VariableProvenance,
)
from pypost.models.models import Collection

pytestmark = pytest.mark.timeout(30)


def test_collection_namespaced_secret_override():
    """Namespaced secrets (e.g. billing.api_key) override base api_key for that collection."""
    manifest = LibraryManifest(
        name="Shared Services Library",
        collections=["collections/billing.yaml", "collections/users.yaml"],
        variables=[
            CollectionVariable(name="api_key", default="default-shared-key", secret=True)
        ],
    )
    billing_col = Collection(name="billing")
    users_col = Collection(name="users")

    overlay = LocalLibraryOverlay(
        library_id=manifest.id,
        secrets={
            "billing.api_key": "billing-secret-123",
            "users.api_key": "users-secret-456",
        },
    )

    resolver = LibraryVariableResolver()

    # Resolve for billing collection
    billing_res = resolver.resolve(manifest=manifest, overlay=overlay, collection=billing_col)
    assert billing_res.variables["api_key"] == "billing-secret-123"
    assert billing_res.provenance["api_key"] == VariableProvenance.LOCAL_SECRET
    assert billing_res.variables["billing.api_key"] == "billing-secret-123"

    # Resolve for users collection
    users_res = resolver.resolve(manifest=manifest, overlay=overlay, collection=users_col)
    assert users_res.variables["api_key"] == "users-secret-456"
    assert users_res.provenance["api_key"] == VariableProvenance.LOCAL_SECRET
    assert users_res.variables["users.api_key"] == "users-secret-456"


def test_collection_namespaced_preset_override():
    """Namespaced preset profiles take precedence for matching collection."""
    manifest = LibraryManifest(
        name="Shared Services Library",
        collections=["collections/billing.yaml"],
        variables=[
            CollectionVariable(name="base_url", default="https://api.example.com")
        ],
        presets={
            "staging": {
                "base_url": "https://default.staging.example.com",
                "billing.base_url": "https://billing.staging.example.com",
            }
        },
    )
    billing_col = Collection(name="billing")
    resolver = LibraryVariableResolver()

    res = resolver.resolve(
        manifest=manifest,
        active_profile="staging",
        collection=billing_col,
    )
    assert res.variables["base_url"] == "https://billing.staging.example.com"
    assert res.provenance["base_url"] == VariableProvenance.PROFILE
    assert res.variables["billing.base_url"] == "https://billing.staging.example.com"


def test_unnamespaced_fallback_when_scoped_override_missing():
    """When no scoped override exists, collection falls back to un-namespaced variable."""
    manifest = LibraryManifest(
        name="Shared Services Library",
        collections=["collections/billing.yaml"],
        variables=[
            CollectionVariable(name="timeout", default="30")
        ],
    )
    overlay = LocalLibraryOverlay(
        library_id=manifest.id,
        overrides={"timeout": "10"},
    )
    billing_col = Collection(name="billing")
    resolver = LibraryVariableResolver()

    res = resolver.resolve(manifest=manifest, overlay=overlay, collection=billing_col)
    assert res.variables["timeout"] == "10"
    assert res.provenance["timeout"] == VariableProvenance.LOCAL_OVERRIDE
