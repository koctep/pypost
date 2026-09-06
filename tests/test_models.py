"""Red repro test for PYPOST-1283: Environment.mcp_overridable_keys default.

`20-architecture.md` requires a new `Environment.mcp_overridable_keys: Set[str]`
field, secure-by-default (`default_factory=set`), so an environment created
before this change — or a variable never explicitly marked — is
non-overridable by an MCP caller. `pypost/models/models.py:136` does not yet
define this field, so constructing a bare `Environment()` and reading
`mcp_overridable_keys` fails with `AttributeError` today — that is the
intended failure reason for this red test, not a fixture/import problem.
"""
from __future__ import annotations

import unittest

import pytest

from pypost.models.models import Environment

pytestmark = pytest.mark.timeout(30)


class TestEnvironmentMcpOverridableKeysDefault(unittest.TestCase):
    def test_bare_environment_defaults_mcp_overridable_keys_to_empty_set(self) -> None:
        env = Environment()
        self.assertEqual(env.mcp_overridable_keys, set())

    def test_existing_environment_missing_field_deserializes_to_empty_set(self) -> None:
        """An environment persisted before this change has no stored field."""
        env = Environment(name="Legacy", variables={"jira_project_key": "PROJ"})
        self.assertEqual(env.mcp_overridable_keys, set())


if __name__ == "__main__":
    unittest.main()
