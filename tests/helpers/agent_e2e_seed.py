"""Helpers for agent e2e seed tests (PYPOST-857)."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

from pypost.fixtures.agent_e2e_seed import (
    SEED_BASE_URL_KEY,
    SEED_BASE_URL_VALUE,
    SEED_COLLECTION_ID,
    SEED_COLLECTION_NAME,
    SEED_ENV_ID,
    SEED_ENV_NAME,
    SEED_GET_REQUEST_ID,
    SEED_GET_REQUEST_NAME,
    SEED_POST_REQUEST_ID,
    SEED_POST_REQUEST_NAME,
    write_agent_e2e_seed,
)

__all__ = [
    "SEED_BASE_URL_KEY",
    "SEED_BASE_URL_VALUE",
    "SEED_COLLECTION_ID",
    "SEED_COLLECTION_NAME",
    "SEED_ENV_ID",
    "SEED_ENV_NAME",
    "SEED_GET_REQUEST_ID",
    "SEED_GET_REQUEST_NAME",
    "SEED_POST_REQUEST_ID",
    "SEED_POST_REQUEST_NAME",
    "seeded_agent_dirs",
    "write_agent_e2e_seed",
]


@contextmanager
def seeded_agent_dirs() -> Iterator[tuple[Path, Path]]:
    """Allocate temp config/data dirs, write seed into data_dir, yield paths."""
    with TemporaryDirectory() as config, TemporaryDirectory() as data:
        config_dir = Path(config)
        data_dir = Path(data)
        write_agent_e2e_seed(data_dir)
        yield config_dir, data_dir
