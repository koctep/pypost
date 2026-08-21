from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Literal, Mapping

from platformdirs import user_data_dir

DaemonPathSource = Literal["cli", "environment", "default"]


class DaemonConfigurationError(Exception):
    def __init__(
        self,
        logical_name: str,
        source: DaemonPathSource,
        path: Path | None,
        reason: str,
    ) -> None:
        self.logical_name = logical_name
        self.source = source
        self.path = path
        self.reason = reason
        path_text = f" path={path}" if path is not None else ""
        super().__init__(f"invalid {logical_name} directory source={source}{path_text}: {reason}")


@dataclass(frozen=True)
class ResolvedDaemonPaths:
    collections_dir: Path
    environments_dir: Path
    collections_source: DaemonPathSource
    environments_source: DaemonPathSource


def _resolve_value(
    *,
    logical_name: str,
    cli_value: str | None,
    environment_value: str | None,
    default: Path,
    cwd: Path,
) -> tuple[Path, DaemonPathSource]:
    source: DaemonPathSource
    if cli_value is not None:
        if not cli_value.strip():
            raise DaemonConfigurationError(logical_name, "cli", None, "empty value")
        selected, source = cli_value, "cli"
    elif environment_value and environment_value.strip():
        selected, source = environment_value, "environment"
    else:
        selected, source = str(default), "default"

    candidate = Path(selected).expanduser()
    if not candidate.is_absolute():
        candidate = cwd / candidate
    try:
        return candidate.resolve(), source
    except (OSError, RuntimeError) as exc:
        raise DaemonConfigurationError(
            logical_name, source, candidate.absolute(), "cannot resolve"
        ) from exc


def resolve_daemon_paths(
    *,
    cli_collections_dir: str | None,
    cli_environments_dir: str | None,
    environ: Mapping[str, str],
    default_data_dir: Path | None = None,
    cwd: Path | None = None,
) -> ResolvedDaemonPaths:
    data_dir = default_data_dir or Path(user_data_dir("pypost"))
    working_dir = cwd or Path.cwd()
    collections_dir, collections_source = _resolve_value(
        logical_name="collections",
        cli_value=cli_collections_dir,
        environment_value=environ.get("PYPOST_COLLECTIONS_DIR"),
        default=data_dir / "collections",
        cwd=working_dir,
    )
    environments_dir, environments_source = _resolve_value(
        logical_name="environments",
        cli_value=cli_environments_dir,
        environment_value=environ.get("PYPOST_ENVIRONMENTS_DIR"),
        default=data_dir,
        cwd=working_dir,
    )
    return ResolvedDaemonPaths(
        collections_dir,
        environments_dir,
        collections_source,
        environments_source,
    )


def _validate_directory(
    logical_name: str,
    path: Path,
    source: DaemonPathSource,
) -> None:
    if source == "default":
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DaemonConfigurationError(
                logical_name, source, path, "cannot initialize"
            ) from exc
    if not path.exists():
        raise DaemonConfigurationError(logical_name, source, path, "does not exist")
    if not path.is_dir():
        raise DaemonConfigurationError(logical_name, source, path, "not a directory")
    if not os.access(path, os.R_OK | os.X_OK):
        raise DaemonConfigurationError(logical_name, source, path, "not readable")


def validate_daemon_paths(paths: ResolvedDaemonPaths) -> None:
    _validate_directory("collections", paths.collections_dir, paths.collections_source)
    _validate_directory("environments", paths.environments_dir, paths.environments_source)
    if paths.environments_source == "default":
        environments_file = paths.environments_dir / "environments.json"
        if not environments_file.exists():
            try:
                environments_file.write_text(json.dumps([]), encoding="utf-8")
            except OSError as exc:
                raise DaemonConfigurationError(
                    "environments",
                    paths.environments_source,
                    paths.environments_dir,
                    "cannot initialize environments.json",
                ) from exc
