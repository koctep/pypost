"""PYPOST-864: guard seed inventory constants vs doc/dev inventory page."""

from __future__ import annotations

from pathlib import Path

import pytest

from pypost.fixtures.agent_e2e_seed import (
    SEED_BASE_URL_KEY,
    SEED_BASE_URL_VALUE,
    SEED_COLLECTION_ID,
    SEED_COLLECTION_NAME,
    SEED_ENV_ID,
    SEED_ENV_NAME,
    SEED_GET_REQUEST_ID,
    SEED_GET_REQUEST_NAME,
    SEED_GET_URL,
    SEED_POST_REQUEST_ID,
    SEED_POST_REQUEST_NAME,
    SEED_POST_URL,
)

pytestmark = pytest.mark.timeout(10)

_INVENTORY_DOC = Path("doc/dev/agent_e2e_seed.md")

# Tokens that must appear in the published inventory (code source of truth).
_INVENTORY_TOKENS: tuple[tuple[str, str], ...] = (
    ("SEED_COLLECTION_ID", SEED_COLLECTION_ID),
    ("SEED_COLLECTION_NAME", SEED_COLLECTION_NAME),
    ("SEED_ENV_ID", SEED_ENV_ID),
    ("SEED_ENV_NAME", SEED_ENV_NAME),
    ("SEED_GET_REQUEST_ID", SEED_GET_REQUEST_ID),
    ("SEED_GET_REQUEST_NAME", SEED_GET_REQUEST_NAME),
    ("SEED_POST_REQUEST_ID", SEED_POST_REQUEST_ID),
    ("SEED_POST_REQUEST_NAME", SEED_POST_REQUEST_NAME),
    ("SEED_BASE_URL_KEY", SEED_BASE_URL_KEY),
    ("SEED_BASE_URL_VALUE", SEED_BASE_URL_VALUE),
    ("SEED_GET_URL", SEED_GET_URL),
    ("SEED_POST_URL", SEED_POST_URL),
)


def test_seed_inventory_constants_match_doc() -> None:
    """Inventory constants in code must appear in doc/dev/agent_e2e_seed.md."""
    assert _INVENTORY_DOC.is_file(), f"missing inventory doc: {_INVENTORY_DOC}"
    text = _INVENTORY_DOC.read_text(encoding="utf-8")
    assert "## Inventory after bootstrap" in text, (
        f"{_INVENTORY_DOC}: missing '## Inventory after bootstrap' section"
    )
    for const_name, token in _INVENTORY_TOKENS:
        assert token in text, (
            f"{_INVENTORY_DOC}: missing inventory token for {const_name}={token!r}"
        )
