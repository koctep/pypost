"""Unit tests for shared Makefile contract parsers (PYPOST-937)."""

from __future__ import annotations

import pytest

from tests.makefile_contract_helpers import (
    makefile_target_help_comment,
    makefile_target_recipe_body,
)
from tests.test_makefile import MAKEFILE

pytestmark = pytest.mark.timeout(10)

_TEST_AGENT_E2E = "test-agent-e2e"
_TEST = "test"


def test_help_comment_parses_test_agent_e2e_target() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")
    help_text = makefile_target_help_comment(text, _TEST_AGENT_E2E)
    lower = help_text.lower()
    assert "broader" in lower
    assert "beyond golden" in lower


def test_recipe_body_parses_test_agent_e2e_target() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")
    recipe = makefile_target_recipe_body(text, _TEST_AGENT_E2E)
    assert '-m "agent_e2e and not slow"' in recipe


def test_help_comment_parses_test_target() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")
    help_text = makefile_target_help_comment(text, _TEST)
    assert "fast test suite" in help_text.lower()


def test_recipe_body_parses_test_target() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")
    recipe = makefile_target_recipe_body(text, _TEST)
    assert '-m "not slow"' in recipe
