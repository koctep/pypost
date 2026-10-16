"""Failing repro test for reusable multi-subsystem integration harness helper (PYPOST-1417).

Asserts the contracts specified in ai-tasks/PYPOST-1417/20-architecture.md:
- Harness importability and cross-subsystem service initialization.
- Context manager lifecycle with deterministic registry server cleanup.
- Pytest fixture binding and automated teardown.
- Unified multi-subsystem end-to-end execution orchestration.
"""

from __future__ import annotations

import logging
from pathlib import Path
import pytest

from pypost.core.collection_variable_import import ConflictStrategy
from tests.helpers.collection_integration_harness import (
    CollectionVariablesIntegrationHarness,
    UnifiedLifecycleResult,
    collection_integration_harness,
)

pytestmark = pytest.mark.timeout(30)


@pytest.mark.timeout(30)
def test_harness_import_and_instantiation(tmp_path: Path) -> None:
    """Validate importability and filesystem/service initialization of the harness."""
    harness = CollectionVariablesIntegrationHarness(tmp_path)
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


@pytest.mark.timeout(30)
def test_harness_context_manager_lifecycle_and_teardown(tmp_path: Path) -> None:
    """Validate context manager __enter__/__exit__ and automated server registry teardown."""
    col_dict = {
        "id": "col-cm-test",
        "name": "CM Test Collection",
        "variables": [
            {
                "name": "base_url",
                "type": "string",
                "default": "https://api.example.com",
                "required": True,
                "secret": False,
            }
        ],
        "requests": [
            {
                "name": "ping",
                "url": "{{base_url}}/ping",
                "method": "GET",
            }
        ],
    }

    server_id: str = ""
    with CollectionVariablesIntegrationHarness(tmp_path) as harness:
        harness.create_library(
            manifest_id="lib-cm-test",
            is_legacy_manifest=False,
            collections_data={"col-cm-test.json": col_dict},
        )
        server_id, port, status = harness.start_standalone_server(
            manifest_id="lib-cm-test",
            collection_id="col-cm-test",
            collection_filename="col-cm-test.json",
        )
        assert port > 0
        assert status == "running"
        assert harness.registry.is_running(server_id) is True

    # After exiting the context manager, server must be stopped
    assert harness.registry.is_running(server_id) is False
    assert harness.registry.status(server_id).state == "stopped"

    # Idempotent cleanup calls must not raise exceptions
    harness.teardown()
    harness.close()


@pytest.mark.timeout(30)
def test_pytest_fixture_lifecycle_binding(tmp_path: Path) -> None:
    """Validate pytest fixture binding yields initialized harness and cleans up."""
    fixture_gen = collection_integration_harness(tmp_path)
    harness = next(fixture_gen)
    assert harness.tmp_path.is_dir()
    assert harness.libraries_dir.is_dir()
    assert harness.workspace_dir.is_dir()
    assert harness.overlay_dir.is_dir()
    assert harness.storage_manager is not None
    assert harness.registry is not None
    assert harness.library_service is not None

    env = harness.create_workspace_environment(
        name="Fixture Test Env",
        variables={"HOST": "localhost"},
    )
    assert env.name == "Fixture Test Env"
    saved = harness.storage_manager.load_environments()
    assert any(e.name == "Fixture Test Env" for e in saved)

    # Validate fixture cleanup terminates generator cleanly
    with pytest.raises(StopIteration):
        next(fixture_gen)


@pytest.mark.timeout(30)
def test_unified_lifecycle_execution(tmp_path: Path) -> None:
    """Validate end-to-end unified lifecycle execution across multi-subsystem stack."""
    col_dict = {
        "id": "col-unified-test",
        "name": "Unified Auth Service",
        "variables": [
            {
                "name": "base_url",
                "type": "string",
                "default": "https://api.example.com",
                "required": True,
                "secret": False,
            },
            {
                "name": "api_token",
                "type": "string",
                "default": "default-token",
                "required": True,
                "secret": True,
            },
        ],
        "presets": {
            "staging": {
                "base_url": "https://staging.example.com",
                "api_token": "staging-token-456",
            },
        },
        "requests": [
            {
                "name": "get_user",
                "url": "{{base_url}}/v1/user",
                "headers": {"Authorization": "Bearer {{api_token}}"},
                "body": "{\"env\": \"staging\"}",
            }
        ],
    }

    with CollectionVariablesIntegrationHarness(tmp_path) as harness:
        result = harness.run_unified_lifecycle(
            manifest_id="lib-unified",
            collection_data=col_dict,
            active_profile="staging",
            overlay_secrets={"api_token": "staging-token-456"},
            workspace_env_name="Staging Env",
            conflict_strategy=ConflictStrategy.OVERWRITE,
        )

        assert isinstance(result, UnifiedLifecycleResult)
        assert result.status == "success"
        assert result.standalone_server_id.startswith("standalone-lib-unified")
        assert result.standalone_status == "running"
        assert result.rendered_request_url == "https://staging.example.com/v1/user"
        assert result.rendered_auth_header == "Bearer staging-token-456"
        assert result.rendered_body == "{\"env\": \"staging\"}"


@pytest.mark.timeout(30)
def test_harness_observability_and_secret_redaction(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Validate structured logging, lifecycle traceability, and secret redaction in harness."""
    secret_val = "super_secret_overlay_token_12345"
    with caplog.at_level(logging.DEBUG, logger="tests.helpers.collection_integration_harness"):
        with CollectionVariablesIntegrationHarness(tmp_path) as harness:
            harness.create_library(
                manifest_id="lib-obs",
                is_legacy_manifest=False,
                collections_data={
                    "col.json": {
                        "id": "col-obs",
                        "variables": [],
                        "requests": [],
                    }
                },
            )
            harness.create_overlay(
                library_id="lib-obs",
                active_profile="dev",
                secrets={"token": secret_val},
            )
            harness.create_workspace_environment(
                name="Env Obs",
                variables={"token": secret_val},
                hidden_keys={"token"},
            )

    messages = [r.message for r in caplog.records]
    assert any("Initialized CollectionVariablesIntegrationHarness" in m for m in messages)
    assert any("Entered harness context manager scope" in m for m in messages)
    assert any("Created library manifest_id=lib-obs" in m for m in messages)
    assert any("Created local library overlay for library_id=lib-obs" in m for m in messages)
    assert any("Created workspace environment name=Env Obs" in m for m in messages)
    assert any("Tearing down harness and stopping all registered servers" in m for m in messages)

    # Secret Redaction: Verify secret value is never logged in plaintext
    for record in caplog.records:
        assert secret_val not in record.message, f"Secret leaked in log: {record.message}"
