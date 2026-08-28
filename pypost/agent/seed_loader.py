"""Seed collection and environment loader for agent sidecar sessions (PYPOST-993)."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import time
from typing import Any, Final

from pydantic import ValidationError
import yaml

from pypost.core.storage import StorageManager
from pypost.models.models import Collection, Environment

logger = logging.getLogger(__name__)

DEFAULT_SEED_ENV_VAR: Final[str] = "PYPOST_AGENT_SEED_PATH"


class SeedLoadError(RuntimeError):
    """Raised when a seed path cannot be resolved, read, or parsed."""


class SeedFormatError(SeedLoadError):
    """Raised when a seed file or directory has invalid format or schema."""


@dataclass(frozen=True)
class SeedInjectionSummary:
    """Summary of items successfully injected into workspace storage."""

    collections_count: int
    environments_count: int
    collection_ids: list[str]
    environment_ids: list[str]


def resolve_seed_path(
    cli_path: Path | str | None = None,
    env_var: str = DEFAULT_SEED_ENV_VAR,
) -> Path | None:
    """Resolve seed path giving precedence to CLI argument over environment variable."""
    if cli_path is not None and str(cli_path).strip():
        return Path(cli_path)
    env_val = os.environ.get(env_var)
    if env_val is not None and env_val.strip():
        return Path(env_val.strip())
    return None


def _parse_payload(path: Path) -> Any:
    """Read and parse a JSON or YAML file into a Python object."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SeedLoadError(f"Failed to read seed file {path}: {exc}") from exc

    if not text.strip():
        raise SeedFormatError(f"Seed file {path} is empty")

    try:
        return json.loads(text)
    except Exception:
        try:
            return yaml.safe_load(text)
        except Exception as exc:
            raise SeedFormatError(
                f"Failed to parse seed file as JSON/YAML {path}: {exc}"
            ) from exc


def _is_environment_dict(data: dict[str, Any]) -> bool:
    """Return True if dictionary matches environment structure (variables present, no requests)."""
    return (
        "variables" in data
        and isinstance(data.get("variables"), dict)
        and "requests" not in data
    )


def _inject_file(storage: StorageManager, file_path: Path) -> tuple[list[Path], int]:
    """Validate and inject a single file (collection or environment) into storage.

    Returns a tuple of (written_collection_paths, request_count).
    """
    data = _parse_payload(file_path)
    written: list[Path] = []

    if isinstance(data, dict):
        if _is_environment_dict(data):
            try:
                env = Environment(**data)
            except ValidationError as exc:
                raise SeedFormatError(
                    f"Seed file {file_path} failed Environment validation: {exc}"
                ) from exc
            storage.save_environments([env])
            logger.info(
                "agent_seed_injected_environment file=%s env_id=%s",
                file_path,
                env.id,
            )
            return written, 0

        try:
            col = Collection(**data)
        except ValidationError as exc:
            raise SeedFormatError(
                f"Seed file {file_path} failed Collection validation: {exc}"
            ) from exc
        storage.save_collection(col)
        out_path = storage._collection_path_by_id(col.id)
        written.append(out_path)
        req_count = len(col.requests)
        logger.info(
            "agent_seed_injected_collection file=%s collection_id=%s request_count=%d",
            file_path,
            col.id,
            req_count,
        )
        return written, req_count

    if isinstance(data, list):
        if not data:
            raise SeedFormatError(f"Seed file {file_path} contains an empty list")

        if all(isinstance(item, dict) and _is_environment_dict(item) for item in data):
            try:
                envs = [Environment(**item) for item in data]
            except ValidationError as exc:
                raise SeedFormatError(
                    f"Seed file {file_path} failed Environment validation: {exc}"
                ) from exc
            storage.save_environments(envs)
            logger.info(
                "agent_seed_injected_environments file=%s count=%d",
                file_path,
                len(envs),
            )
            return written, 0

        total_requests = 0
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                raise SeedFormatError(f"Item #{idx} in {file_path} is not an object")
            try:
                col = Collection(**item)
            except ValidationError as exc:
                raise SeedFormatError(
                    f"Item #{idx} in {file_path} failed Collection validation: {exc}"
                ) from exc
            storage.save_collection(col)
            out_path = storage._collection_path_by_id(col.id)
            written.append(out_path)
            col_reqs = len(col.requests)
            total_requests += col_reqs
            logger.info(
                "agent_seed_injected_collection file=%s index=%d collection_id=%s request_count=%d",
                file_path,
                idx,
                col.id,
                col_reqs,
            )
        return written, total_requests

    raise SeedFormatError(
        f"Seed file {file_path} root must be object or list, got {type(data).__name__}"
    )


def inject_seed(data_dir: Path, seed_path: Path | str | None) -> list[Path]:
    """Parse seed data from seed_path and write into data_dir.

    Args:
        data_dir: Target PyPost data directory (where collections/ and environments.json live).
        seed_path: Path to seed JSON/YAML file or directory.

    Returns:
        List of Path objects for all written collection JSON files.

    Raises:
        SeedLoadError: If seed_path does not exist or cannot be read.
        SeedFormatError: If seed data contains invalid JSON/YAML or schema mismatch.
    """
    if seed_path is None:
        return []

    start_time = time.perf_counter()
    target_dir = Path(data_dir)
    source = Path(seed_path)
    if not source.exists():
        raise SeedLoadError(f"Seed path does not exist: {source}")

    storage = StorageManager(data_dir=target_dir)

    if source.is_file():
        written, total_requests = _inject_file(storage, source)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            "agent_seed_injection_completed seed_path=%s collection_count=%d "
            "request_count=%d duration_ms=%.2f",
            source,
            len(written),
            total_requests,
            duration_ms,
        )
        return written

    if source.is_dir():
        written: list[Path] = []
        total_requests = 0
        environments_injected = False

        env_file = source / "environments.json"
        if env_file.is_file():
            env_data = _parse_payload(env_file)
            if isinstance(env_data, list):
                try:
                    envs = [Environment(**item) for item in env_data]
                except ValidationError as exc:
                    raise SeedFormatError(
                        f"Failed validating environments from {env_file}: {exc}"
                    ) from exc
            elif isinstance(env_data, dict):
                try:
                    envs = [Environment(**env_data)]
                except ValidationError as exc:
                    raise SeedFormatError(
                        f"Failed validating environment from {env_file}: {exc}"
                    ) from exc
            else:
                raise SeedFormatError(
                    f"Invalid environments root type in {env_file}: {type(env_data).__name__}"
                )
            storage.save_environments(envs)
            environments_injected = True
            logger.info(
                "agent_seed_injected_environments file=%s count=%d",
                env_file,
                len(envs),
            )

        collections_sub = source / "collections"
        candidate_dir = collections_sub if collections_sub.is_dir() else source

        for candidate_file in sorted(candidate_dir.iterdir()):
            if not candidate_file.is_file():
                continue
            if candidate_file.name == "environments.json":
                continue
            if candidate_file.suffix.lower() not in (".json", ".yaml", ".yml"):
                continue
            sub_written, sub_requests = _inject_file(storage, candidate_file)
            written.extend(sub_written)
            total_requests += sub_requests

        if not written and not environments_injected:
            raise SeedFormatError(
                f"No valid collection or environment seeds found in directory: {source}"
            )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            "agent_seed_injection_completed seed_path=%s collection_count=%d "
            "request_count=%d duration_ms=%.2f",
            source,
            len(written),
            total_requests,
            duration_ms,
        )
        return written

    raise SeedLoadError(
        f"Seed path is neither a regular file nor a directory: {source}"
    )
