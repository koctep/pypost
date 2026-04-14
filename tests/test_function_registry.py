import unittest

from jinja2 import Environment

from pypost.core.function_registry import FunctionRegistry


class TestFunctionRegistry(unittest.TestCase):
    def test_allowed_names_matches_catalog(self):
        reg = FunctionRegistry()
        self.assertEqual(reg.allowed_names(), frozenset({"urlencode", "md5", "base64"}))

    def test_is_allowed(self):
        reg = FunctionRegistry()
        self.assertTrue(reg.is_allowed("md5"))
        self.assertFalse(reg.is_allowed("not_allowed"))

    def test_get_returns_callable_or_none(self):
        reg = FunctionRegistry()
        self.assertIsNotNone(reg.get("urlencode"))
        self.assertEqual(reg.get("missing"), None)

    def test_register_into_env_only_sets_catalog_keys(self):
        reg = FunctionRegistry()
        env = Environment()
        env.globals["other"] = "keep"
        reg.register_into_env(env)
        self.assertEqual(env.globals["other"], "keep")
        self.assertEqual(env.globals["urlencode"]("a b"), "a%20b")

    def test_register_into_env_repeat_rebinds_catalog_only(self):
        reg = FunctionRegistry()
        env = Environment()
        env.globals["other"] = 1
        reg.register_into_env(env)
        first = env.globals["md5"]
        reg.register_into_env(env)
        self.assertEqual(env.globals["other"], 1)
        self.assertIs(env.globals["md5"], first)


if __name__ == "__main__":
    unittest.main()
