#!/usr/bin/env python3
"""Generate committed MCP test collection and environment fixtures (PYPOST-179)."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pypost.fixtures.mcp_test_fixtures import (  # noqa: E402
    MCP_COLLECTION_PATH,
    MCP_TEST_ENV_PATH,
    build_mcp_test_collection,
    build_mcp_test_environments,
    fixtures_match_committed,
    serialize_collection,
    serialize_environments,
)

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
    )


def _write_fixtures() -> None:
    collection_text = serialize_collection(build_mcp_test_collection())
    environments_text = serialize_environments(build_mcp_test_environments())

    MCP_COLLECTION_PATH.parent.mkdir(parents=True, exist_ok=True)
    MCP_TEST_ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    MCP_COLLECTION_PATH.write_text(collection_text, encoding="utf-8")
    MCP_TEST_ENV_PATH.write_text(environments_text, encoding="utf-8")

    logger.info("Wrote %s", MCP_COLLECTION_PATH.relative_to(_REPO_ROOT))
    logger.info("Wrote %s", MCP_TEST_ENV_PATH.relative_to(_REPO_ROOT))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate MCP test collection and environment JSON fixtures.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 0 when committed files match generated models; 1 otherwise.",
    )
    args = parser.parse_args(argv)
    _configure_logging()

    if args.check:
        if fixtures_match_committed():
            logger.info("Committed MCP test fixtures are up to date.")
            return 0
        logger.error("Committed MCP test fixtures are out of date. Run without --check.")
        return 1

    _write_fixtures()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
