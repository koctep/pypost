"""Unit tests for pypost.agent.seed_loader (PYPOST-993)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
import yaml

from pypost.agent.seed_loader import (
    DEFAULT_SEED_ENV_VAR,
    SeedFormatError,
    SeedLoadError,
    inject_seed,
    resolve_seed_path,
)
from pypost.core.storage import StorageManager

pytestmark = [
    pytest.mark.timeout(60),
]


@pytest.mark.timeout(60)
def test_resolve_seed_path_precedence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cli_file = tmp_path / "cli.json"
    env_file = tmp_path / "env.json"
    cli_file.touch()
    env_file.touch()

    # CLI only
    monkeypatch.delenv(DEFAULT_SEED_ENV_VAR, raising=False)
    assert resolve_seed_path(cli_file) == cli_file

    # Env only
    monkeypatch.setenv(DEFAULT_SEED_ENV_VAR, str(env_file))
    assert resolve_seed_path(None) == env_file

    # CLI overrides env
    assert resolve_seed_path(cli_file) == cli_file

    # Neither
    monkeypatch.delenv(DEFAULT_SEED_ENV_VAR, raising=False)
    assert resolve_seed_path(None) is None
    assert resolve_seed_path("") is None


@pytest.mark.timeout(60)
def test_inject_seed_none_returns_empty(tmp_path: Path) -> None:
    assert inject_seed(tmp_path, None) == []


@pytest.mark.timeout(60)
def test_inject_seed_nonexistent_path_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(SeedLoadError, match="Seed path does not exist"):
        inject_seed(tmp_path, missing)


@pytest.mark.timeout(60)
def test_inject_seed_empty_file_raises(tmp_path: Path) -> None:
    empty = tmp_path / "empty.json"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(SeedFormatError, match="empty"):
        inject_seed(tmp_path, empty)


@pytest.mark.timeout(60)
def test_inject_seed_corrupted_content_raises(tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{not valid json or yaml: : :", encoding="utf-8")
    with pytest.raises(SeedFormatError, match="Failed to parse seed file"):
        inject_seed(tmp_path, corrupt)


@pytest.mark.timeout(60)
def test_inject_seed_single_collection_json(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    seed_file = tmp_path / "seed.json"
    payload = {
        "id": "col-123",
        "name": "Single Col",
        "requests": [
            {"id": "req-1", "name": "Req 1", "method": "GET", "url": "https://example.test"}
        ],
    }
    seed_file.write_text(json.dumps(payload), encoding="utf-8")

    written = inject_seed(data_dir, seed_file)
    assert len(written) == 1
    assert written[0].name == "col-123.json"

    storage = StorageManager(data_dir=data_dir)
    cols = storage.load_collections()
    assert len(cols) == 1
    assert cols[0].id == "col-123"
    assert cols[0].name == "Single Col"
    assert len(cols[0].requests) == 1


@pytest.mark.timeout(60)
def test_inject_seed_single_collection_yaml(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    seed_file = tmp_path / "seed.yaml"
    payload = {
        "id": "col-yaml",
        "name": "YAML Col",
        "requests": [
            {
                "id": "req-y",
                "name": "YAML GET",
                "method": "GET",
                "url": "https://example.test/yaml",
            }
        ],
    }
    seed_file.write_text(yaml.safe_dump(payload), encoding="utf-8")

    written = inject_seed(data_dir, seed_file)
    assert len(written) == 1
    assert written[0].name == "col-yaml.json"

    storage = StorageManager(data_dir=data_dir)
    cols = storage.load_collections()
    assert len(cols) == 1
    assert cols[0].id == "col-yaml"
    assert cols[0].name == "YAML Col"


@pytest.mark.timeout(60)
def test_inject_seed_collection_list(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    seed_file = tmp_path / "collections.json"
    payload = [
        {"id": "col-a", "name": "Collection A", "requests": []},
        {"id": "col-b", "name": "Collection B", "requests": []},
    ]
    seed_file.write_text(json.dumps(payload), encoding="utf-8")

    written = inject_seed(data_dir, seed_file)
    assert len(written) == 2
    assert {p.name for p in written} == {"col-a.json", "col-b.json"}

    storage = StorageManager(data_dir=data_dir)
    cols = storage.load_collections()
    assert {c.id for c in cols} == {"col-a", "col-b"}


@pytest.mark.timeout(60)
def test_inject_seed_environments_file(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    seed_file = tmp_path / "environments.json"
    payload = [
        {"id": "env-1", "name": "Dev Env", "variables": {"host": "dev.local"}},
        {"id": "env-2", "name": "Prod Env", "variables": {"host": "prod.local"}},
    ]
    seed_file.write_text(json.dumps(payload), encoding="utf-8")

    written = inject_seed(data_dir, seed_file)
    assert written == []

    storage = StorageManager(data_dir=data_dir)
    envs = storage.load_environments()
    assert len(envs) == 2
    assert {e.name for e in envs} == {"Dev Env", "Prod Env"}


@pytest.mark.timeout(60)
def test_inject_seed_directory_with_subfolder(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    seed_dir = tmp_path / "seed_bundle"
    cols_dir = seed_dir / "collections"
    cols_dir.mkdir(parents=True)

    col_1 = {"id": "c-1", "name": "Bundle Col 1", "requests": []}
    col_2 = {"id": "c-2", "name": "Bundle Col 2", "requests": []}
    (cols_dir / "c1.json").write_text(json.dumps(col_1), encoding="utf-8")
    (cols_dir / "c2.yaml").write_text(yaml.safe_dump(col_2), encoding="utf-8")

    env_payload = [{"id": "e-1", "name": "Bundle Env", "variables": {"x": "1"}}]
    (seed_dir / "environments.json").write_text(json.dumps(env_payload), encoding="utf-8")

    written = inject_seed(data_dir, seed_dir)
    assert len(written) == 2

    storage = StorageManager(data_dir=data_dir)
    cols = storage.load_collections()
    assert {c.id for c in cols} == {"c-1", "c-2"}
    envs = storage.load_environments()
    assert len(envs) == 1
    assert envs[0].id == "e-1"


@pytest.mark.timeout(60)
def test_inject_seed_empty_directory_raises(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    empty_dir = tmp_path / "empty_seed"
    empty_dir.mkdir()

    with pytest.raises(SeedFormatError, match="No valid collection or environment seeds"):
        inject_seed(data_dir, empty_dir)


@pytest.mark.timeout(60)
def test_inject_seed_observability_logging(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """inject_seed emits structured logs with seed_path, counts, and duration_ms."""
    data_dir = tmp_path / "data"
    seed_file = tmp_path / "seed.json"
    payload = {
        "id": "obs-col-1",
        "name": "Obs Collection",
        "requests": [
            {"id": "r1", "name": "Req 1", "method": "GET", "url": "https://example.test/1"},
            {"id": "r2", "name": "Req 2", "method": "POST", "url": "https://example.test/2"},
        ],
    }
    seed_file.write_text(json.dumps(payload), encoding="utf-8")

    with caplog.at_level(logging.INFO, logger="pypost.agent.seed_loader"):
        written = inject_seed(data_dir, seed_file)

    assert len(written) == 1
    assert any(
        "agent_seed_injected_collection" in r.message
        and "collection_id=obs-col-1" in r.message
        and "request_count=2" in r.message
        for r in caplog.records
    )
    assert any(
        "agent_seed_injection_completed" in r.message
        and "collection_count=1" in r.message
        and "request_count=2" in r.message
        and "duration_ms=" in r.message
        for r in caplog.records
    )
