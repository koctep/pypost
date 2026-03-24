"""Tests for pypost.core.environment_ops."""

import unittest

from pypost.core.environment_ops import clone_environment
from pypost.models.models import Environment


class TestCloneEnvironment(unittest.TestCase):
    def test_new_id_and_name(self) -> None:
        source = Environment(name="prod", variables={"a": "1"}, enable_mcp=True)
        clone = clone_environment(source, "prod copy")
        self.assertNotEqual(clone.id, source.id)
        self.assertEqual(clone.name, "prod copy")

    def test_strips_name(self) -> None:
        source = Environment(name="a", variables={})
        clone = clone_environment(source, "  b  ")
        self.assertEqual(clone.name, "b")

    def test_copies_variables_and_mcp(self) -> None:
        source = Environment(
            name="s",
            variables={"x": "y", "k": "v"},
            enable_mcp=True,
        )
        clone = clone_environment(source, "c")
        self.assertEqual(clone.variables, source.variables)
        self.assertTrue(clone.enable_mcp)

    def test_variables_dict_is_independent(self) -> None:
        source = Environment(name="s", variables={"k": "v"})
        clone = clone_environment(source, "c")
        clone.variables["k"] = "changed"
        self.assertEqual(source.variables["k"], "v")


if __name__ == "__main__":
    unittest.main()
