"""Tests for pypost.core.environment_ops."""

import pytest

import unittest

from pypost.core.environment_messages import (
    MSG_EMPTY_NAME,
    format_duplicate_environment_name,
)
from pypost.core.environment_ops import (
    clone_environment,
    clone_environments,
    validate_environment_rename,
    validate_environment_variable_name,
)
from pypost.models.models import Environment

pytestmark = pytest.mark.timeout(60)


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

    def test_copies_hidden_keys_and_is_independent(self) -> None:
        source = Environment(
            name="s",
            variables={"API_KEY": "secret"},
            hidden_keys={"API_KEY"},
        )
        clone = clone_environment(source, "c")
        self.assertEqual(clone.hidden_keys, {"API_KEY"})
        clone.hidden_keys.add("ANOTHER")
        self.assertEqual(source.hidden_keys, {"API_KEY"})

    def test_environment_backward_compat_without_hidden_keys(self) -> None:
        env = Environment(**{"name": "legacy", "variables": {"A": "1"}})
        self.assertEqual(env.hidden_keys, set())

    def test_environment_dump_and_load_preserves_hidden_keys(self) -> None:
        source = Environment(
            name="prod",
            variables={"TOKEN": "abc"},
            hidden_keys={"TOKEN"},
        )
        restored = Environment(**source.model_dump())
        self.assertEqual(restored.hidden_keys, {"TOKEN"})


class TestValidateEnvironmentRename(unittest.TestCase):
    def test_rejects_empty_name(self) -> None:
        accepted, normalized, error = validate_environment_rename(
            "   ",
            "Dev",
            ["Dev"],
            0,
        )
        self.assertFalse(accepted)
        self.assertEqual(normalized, "")
        self.assertEqual(error, MSG_EMPTY_NAME)

    def test_accepts_same_name_no_op(self) -> None:
        accepted, normalized, error = validate_environment_rename(
            "Dev",
            "Dev",
            ["Dev"],
            0,
        )
        self.assertTrue(accepted)
        self.assertEqual(normalized, "Dev")
        self.assertEqual(error, "")

    def test_rejects_duplicate_name(self) -> None:
        accepted, normalized, error = validate_environment_rename(
            "Staging",
            "Dev",
            ["Dev", "Staging"],
            0,
        )
        self.assertFalse(accepted)
        self.assertEqual(normalized, "")
        self.assertEqual(error, format_duplicate_environment_name("Staging"))

    def test_accepts_unique_rename(self) -> None:
        accepted, normalized, error = validate_environment_rename(
            "  Prod  ",
            "Dev",
            ["Dev"],
            0,
        )
        self.assertTrue(accepted)
        self.assertEqual(normalized, "Prod")
        self.assertEqual(error, "")


class TestValidateEnvironmentVariableName(unittest.TestCase):
    def test_accepts_valid_name(self) -> None:
        is_valid, error = validate_environment_variable_name("api_key")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_rejects_empty_name(self) -> None:
        is_valid, error = validate_environment_variable_name("")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Variable name cannot be empty.")

    def test_rejects_name_starting_with_digit(self) -> None:
        is_valid, error = validate_environment_variable_name("1bad")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Variable name cannot start with a digit.")

    def test_rejects_invalid_characters(self) -> None:
        is_valid, error = validate_environment_variable_name("api-key")
        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            "Variable name can only contain letters, numbers, and underscores.",
        )


class TestCloneEnvironments(unittest.TestCase):
    def test_returns_independent_deep_copies(self) -> None:
        source = Environment(
            name="Dev",
            variables={"API_KEY": "secret"},
            hidden_keys={"API_KEY"},
            enable_mcp=True,
        )
        copies = clone_environments([source])
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies[0].id, source.id)
        copies[0].variables["API_KEY"] = "changed"
        copies[0].hidden_keys.add("OTHER")
        copies[0].enable_mcp = False
        copies[0].name = "Staging"
        self.assertEqual(source.variables["API_KEY"], "secret")
        self.assertEqual(source.hidden_keys, {"API_KEY"})
        self.assertTrue(source.enable_mcp)
        self.assertEqual(source.name, "Dev")

    def test_empty_list(self) -> None:
        self.assertEqual(clone_environments([]), [])


if __name__ == "__main__":
    unittest.main()
