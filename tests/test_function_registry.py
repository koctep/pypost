import os
from unittest.mock import patch
import pytest
import unittest

from jinja2 import Environment

from pypost.core.function_registry import FunctionRegistry


pytestmark = pytest.mark.timeout(30)


class TestFunctionRegistry(unittest.TestCase):
    def test_allowed_names_matches_catalog(self):
        reg = FunctionRegistry()
        self.assertEqual(
            reg.allowed_names(),
            frozenset({"urlencode", "md5", "base64", "to_int", "env"}),
        )

    def test_is_allowed(self):
        reg = FunctionRegistry()
        self.assertTrue(reg.is_allowed("md5"))
        self.assertTrue(reg.is_allowed("env"))
        self.assertFalse(reg.is_allowed("not_allowed"))

    def test_get_returns_callable_or_none(self):
        reg = FunctionRegistry()
        self.assertIsNotNone(reg.get("urlencode"))
        self.assertIsNotNone(reg.get("env"))
        self.assertEqual(reg.get("missing"), None)

    def test_env_function_resolves_from_environ(self):
        reg = FunctionRegistry()
        env_fn = reg.get("env")
        self.assertIsNotNone(env_fn)
        with patch.dict(os.environ, {"PYPOST_TEST_KEY": "secret_token_123"}):
            self.assertEqual(env_fn("PYPOST_TEST_KEY"), "secret_token_123")

    def test_env_function_missing_key_returns_empty_string(self):
        reg = FunctionRegistry()
        env_fn = reg.get("env")
        self.assertIsNotNone(env_fn)
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(env_fn("NON_EXISTENT_KEY"), "")

    def test_env_function_converts_input_to_string(self):
        reg = FunctionRegistry()
        env_fn = reg.get("env")
        self.assertIsNotNone(env_fn)
        with patch.dict(os.environ, {"123": "number_env_val", "None": "none_env_val"}):
            self.assertEqual(env_fn(123), "number_env_val")
            self.assertEqual(env_fn(None), "none_env_val")

    def test_register_into_env_only_sets_catalog_keys(self):
        reg = FunctionRegistry()
        env = Environment()
        env.globals["other"] = "keep"
        reg.register_into_env(env)
        self.assertEqual(env.globals["other"], "keep")
        self.assertEqual(env.globals["urlencode"]("a b"), "a%20b")
        with patch.dict(os.environ, {"API_KEY": "my_api_key"}):
            self.assertEqual(env.globals["env"]("API_KEY"), "my_api_key")

    def test_register_into_env_repeat_rebinds_catalog_only(self):
        reg = FunctionRegistry()
        env = Environment()
        env.globals["other"] = 1
        reg.register_into_env(env)
        first = env.globals["md5"]
        first_env = env.globals["env"]
        reg.register_into_env(env)
        self.assertEqual(env.globals["other"], 1)
        self.assertIs(env.globals["md5"], first)
        self.assertIs(env.globals["env"], first_env)

    def test_catalog_allow_list_matches_env_globals(self):
        """Every allowed catalog name is bound on env.globals to its implementation."""
        reg = FunctionRegistry()
        env = Environment()
        reg.register_into_env(env)
        for name in reg.allowed_names():
            self.assertIn(name, env.globals)
            self.assertIs(env.globals[name], reg.get(name))
            self.assertTrue(callable(env.globals[name]))


if __name__ == "__main__":
    unittest.main()
