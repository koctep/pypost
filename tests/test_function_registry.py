import os
from unittest.mock import patch
import pytest
import unittest

from jinja2 import Environment

from pypost.core.function_registry import FunctionRegistry


pytestmark = pytest.mark.timeout(30)


class TestFunctionRegistry(unittest.TestCase):
    def test_register_adds_dynamic_function_and_strict_metadata(self):
        reg = FunctionRegistry()

        def reverse(value: object) -> str:
            return str(value)[::-1]

        registered = reg.register("reverse", reverse, is_strict=True)

        self.assertIs(registered, reverse)
        self.assertTrue(reg.is_allowed("reverse"))
        self.assertTrue(reg.is_strict_conversion("reverse"))
        self.assertIs(reg.get("reverse"), reverse)

    def test_register_can_be_used_as_a_strict_decorator(self):
        reg = FunctionRegistry()

        @reg.register("double", is_strict=True)
        def double(value: object) -> str:
            return f"{value}{value}"

        self.assertEqual(double("x"), "xx")
        self.assertIs(reg.get("double"), double)
        self.assertTrue(reg.is_strict_conversion("double"))

    def test_register_strict_supports_bare_and_named_decorators(self):
        reg = FunctionRegistry()

        @reg.register_strict
        def upper(value: object) -> str:
            return str(value).upper()

        @reg.register_strict("lower")
        def lower(value: object) -> str:
            return str(value).lower()

        self.assertIs(reg.get("upper"), upper)
        self.assertIs(reg.get("lower"), lower)
        self.assertTrue(reg.is_strict_conversion("upper"))
        self.assertTrue(reg.is_strict_conversion("lower"))

    def test_reregister_replaces_callable_and_strictness(self):
        reg = FunctionRegistry()

        def first(value: object) -> object:
            return value

        def second(value: object) -> object:
            return value

        reg.register("replaceable", first, is_strict=True)
        reg.register("replaceable", second)

        self.assertIs(reg.get("replaceable"), second)
        self.assertFalse(reg.is_strict_conversion("replaceable"))

    def test_dynamic_function_is_bound_into_environment(self):
        reg = FunctionRegistry()

        def shout(value: object) -> str:
            return str(value).upper()

        reg.register("shout", shout)
        env = Environment()
        reg.register_into_env(env)

        self.assertEqual(env.globals["shout"]("hello"), "HELLO")

    def test_register_rejects_invalid_name_and_callable(self):
        reg = FunctionRegistry()

        with self.assertRaises(ValueError):
            reg.register("", lambda value: value)
        with self.assertRaises(TypeError):
            reg.register("not_callable", object())
        self.assertFalse(reg.is_allowed("not_callable"))

    def test_allowed_names_matches_catalog(self):
        reg = FunctionRegistry()
        self.assertEqual(
            reg.allowed_names(),
            frozenset(
                {"urlencode", "md5", "base64", "to_int", "env", "to_adf", "to_json_string"}
            ),
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
