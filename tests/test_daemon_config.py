"""Failing configuration resolver repro for PYPOST-1046."""

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(30)


def test_resolve_daemon_paths_applies_precedence_independently(tmp_path):
    widgets_imported_before = "PySide6.QtWidgets" in sys.modules
    from pypost.core.daemon_config import resolve_daemon_paths

    default_data_dir = tmp_path / "default-data"
    cli_collections_dir = tmp_path / "cli-collections"
    environment_collections_dir = tmp_path / "environment-collections"
    environment_environments_dir = tmp_path / "environment-environments"
    for directory in (
        default_data_dir,
        cli_collections_dir,
        environment_collections_dir,
        environment_environments_dir,
    ):
        directory.mkdir()

    paths = resolve_daemon_paths(
        cli_collections_dir=str(cli_collections_dir),
        cli_environments_dir=None,
        environ={
            "PYPOST_COLLECTIONS_DIR": str(environment_collections_dir),
            "PYPOST_ENVIRONMENTS_DIR": str(environment_environments_dir),
        },
        default_data_dir=default_data_dir,
        cwd=tmp_path,
    )

    assert paths.collections_dir == cli_collections_dir.resolve()
    assert paths.collections_source == "cli"
    assert paths.environments_dir == environment_environments_dir.resolve()
    assert paths.environments_source == "environment"
    assert paths.collections_dir != environment_collections_dir.resolve()
    assert paths.collections_dir != (default_data_dir / "collections").resolve()
    assert paths.environments_dir != default_data_dir.resolve()
    assert ("PySide6.QtWidgets" in sys.modules) is widgets_imported_before


@pytest.mark.parametrize(
    ("cli_value", "environment_value", "expected_source", "expected_name"),
    [
        ("cli", "environment", "cli", "cli"),
        (None, "environment", "environment", "environment"),
        (None, "  ", "default", "default-data/collections"),
    ],
)
def test_resolve_daemon_collection_precedence(
    tmp_path,
    cli_value,
    environment_value,
    expected_source,
    expected_name,
):
    from pypost.core.daemon_config import resolve_daemon_paths

    paths = resolve_daemon_paths(
        cli_collections_dir=cli_value,
        cli_environments_dir=None,
        environ={"PYPOST_COLLECTIONS_DIR": environment_value},
        default_data_dir=tmp_path / "default-data",
        cwd=tmp_path,
    )

    assert paths.collections_source == expected_source
    assert paths.collections_dir == (tmp_path / expected_name).resolve()


def test_validate_daemon_paths_rejects_explicit_missing_directory(tmp_path):
    from pypost.core.daemon_config import (
        DaemonConfigurationError,
        resolve_daemon_paths,
        validate_daemon_paths,
    )

    environments_dir = tmp_path / "environments"
    environments_dir.mkdir()
    paths = resolve_daemon_paths(
        cli_collections_dir="missing",
        cli_environments_dir=str(environments_dir),
        environ={},
        default_data_dir=tmp_path / "default-data",
        cwd=tmp_path,
    )

    with pytest.raises(DaemonConfigurationError, match=r"collections.*source=cli.*does not exist"):
        validate_daemon_paths(paths)


def test_validate_daemon_paths_initializes_defaults(tmp_path):
    from pypost.core.daemon_config import resolve_daemon_paths, validate_daemon_paths

    paths = resolve_daemon_paths(
        cli_collections_dir=None,
        cli_environments_dir=None,
        environ={},
        default_data_dir=tmp_path / "default-data",
        cwd=Path.cwd(),
    )
    validate_daemon_paths(paths)

    assert paths.collections_dir.is_dir()
    assert (paths.environments_dir / "environments.json").read_text() == "[]"


def test_validate_daemon_paths_rejects_non_directory(tmp_path):
    from pypost.core.daemon_config import (
        DaemonConfigurationError,
        resolve_daemon_paths,
        validate_daemon_paths,
    )

    collections_file = tmp_path / "collections.json"
    collections_file.write_text("{}", encoding="utf-8")
    environments_dir = tmp_path / "environments"
    environments_dir.mkdir()
    paths = resolve_daemon_paths(
        cli_collections_dir=str(collections_file),
        cli_environments_dir=str(environments_dir),
        environ={},
        cwd=tmp_path,
    )

    with pytest.raises(DaemonConfigurationError, match="not a directory"):
        validate_daemon_paths(paths)


def test_validate_daemon_paths_rejects_injected_unreadable_directory(
    monkeypatch, tmp_path
):
    from pypost.core.daemon_config import (
        DaemonConfigurationError,
        resolve_daemon_paths,
        validate_daemon_paths,
    )

    collections_dir = tmp_path / "collections"
    environments_dir = tmp_path / "environments"
    collections_dir.mkdir()
    environments_dir.mkdir()
    paths = resolve_daemon_paths(
        cli_collections_dir=str(collections_dir),
        cli_environments_dir=str(environments_dir),
        environ={},
        cwd=tmp_path,
    )
    monkeypatch.setattr("pypost.core.daemon_config.os.access", lambda *_args: False)

    with pytest.raises(DaemonConfigurationError, match=r"collections.*not readable"):
        validate_daemon_paths(paths)


def test_validate_daemon_paths_reports_default_initialization_failure(
    monkeypatch, tmp_path
):
    from pypost.core.daemon_config import (
        DaemonConfigurationError,
        resolve_daemon_paths,
        validate_daemon_paths,
    )

    paths = resolve_daemon_paths(
        cli_collections_dir=None,
        cli_environments_dir=None,
        environ={},
        default_data_dir=tmp_path / "default-data",
        cwd=tmp_path,
    )

    def fail_initialization(_path, *_args, **_kwargs):
        raise OSError("denied")

    monkeypatch.setattr(Path, "mkdir", fail_initialization)

    with pytest.raises(DaemonConfigurationError, match=r"collections.*cannot initialize"):
        validate_daemon_paths(paths)


def test_resolve_daemon_paths_expands_home_directory(tmp_path):
    from pypost.core.daemon_config import resolve_daemon_paths

    paths = resolve_daemon_paths(
        cli_collections_dir="~/daemon-collections",
        cli_environments_dir="~/daemon-environments",
        environ={},
        cwd=tmp_path,
    )

    assert paths.collections_dir == (Path.home() / "daemon-collections").resolve()
    assert paths.environments_dir == (Path.home() / "daemon-environments").resolve()


def test_invalid_cli_directory_never_falls_back_to_valid_environment(tmp_path):
    from pypost.core.daemon_config import (
        DaemonConfigurationError,
        resolve_daemon_paths,
        validate_daemon_paths,
    )

    environment_collections = tmp_path / "environment-collections"
    environments_dir = tmp_path / "environments"
    environment_collections.mkdir()
    environments_dir.mkdir()
    paths = resolve_daemon_paths(
        cli_collections_dir="missing-cli",
        cli_environments_dir=str(environments_dir),
        environ={"PYPOST_COLLECTIONS_DIR": str(environment_collections)},
        cwd=tmp_path,
    )

    with pytest.raises(DaemonConfigurationError) as raised:
        validate_daemon_paths(paths)

    assert raised.value.source == "cli"
    assert raised.value.path == (tmp_path / "missing-cli").resolve()
