"""Tests for ScriptContext and ScriptExecutor (PYPOST-720)."""
import pytest
import unittest

from pypost.core.script_executor import ScriptContext, ScriptExecutor
from pypost.models.models import RequestData
from pypost.models.response import ResponseData

pytestmark = pytest.mark.timeout(30)


class TestScriptContext(unittest.TestCase):
    def _make(self, vars=None):
        return ScriptContext(vars or {"key": "value"})

    def test_init_copies_variables(self):
        original = {"a": "1"}
        ctx = ScriptContext(original)
        original["b"] = "2"
        self.assertNotIn("b", ctx._variables)

    def test_env_property_returns_self(self):
        ctx = self._make()
        self.assertIs(ctx.env, ctx)

    def test_set_updates_variable_and_marks_modified(self):
        ctx = self._make({})
        ctx.set("token", "abc")
        self.assertEqual(ctx._variables["token"], "abc")
        self.assertTrue(ctx.is_modified())

    def test_set_coerces_to_str(self):
        ctx = self._make({})
        ctx.set(1, 42)
        self.assertEqual(ctx._variables["1"], "42")

    def test_get_returns_existing(self):
        ctx = self._make({"x": "hello"})
        self.assertEqual(ctx.get("x"), "hello")

    def test_get_returns_default_for_missing(self):
        ctx = self._make({})
        self.assertIsNone(ctx.get("missing"))
        self.assertEqual(ctx.get("missing", "fallback"), "fallback")

    def test_log_appends_message(self):
        ctx = self._make({})
        ctx.log("hello")
        ctx.log(42)
        self.assertEqual(ctx.get_logs(), ["hello", "42"])

    def test_get_variables_returns_current_state(self):
        ctx = self._make({"a": "1"})
        ctx.set("b", "2")
        self.assertEqual(ctx.get_variables(), {"a": "1", "b": "2"})

    def test_is_modified_false_before_set(self):
        ctx = self._make({"x": "y"})
        self.assertFalse(ctx.is_modified())


class TestScriptExecutor(unittest.TestCase):
    def _req(self):
        return RequestData(name="test", method="GET", url="http://x")

    def _resp(self, status=200, body="ok"):
        return ResponseData(status_code=status, headers={}, body=body, elapsed_time=0.0, size=len(body))

    def test_empty_script_returns_original_vars(self):
        variables = {"env": "prod"}
        updated, logs, err = ScriptExecutor.execute("", self._req(), self._resp(), variables)
        self.assertIs(updated, variables)
        self.assertEqual(logs, [])
        self.assertIsNone(err)

    def test_whitespace_only_script_is_treated_as_empty(self):
        variables = {"x": "1"}
        updated, logs, err = ScriptExecutor.execute("   \n  ", self._req(), self._resp(), variables)
        self.assertIs(updated, variables)

    def test_script_with_variable_modification_returns_updated_vars(self):
        script = "pypost.set('token', 'abc123')"
        variables = {}
        updated, logs, err = ScriptExecutor.execute(script, self._req(), self._resp(), variables)
        self.assertIsNotNone(updated)
        self.assertEqual(updated["token"], "abc123")
        self.assertIsNone(err)

    def test_script_without_modification_returns_none_for_vars(self):
        script = "x = 1 + 1"
        variables = {"a": "b"}
        updated, logs, err = ScriptExecutor.execute(script, self._req(), self._resp(), variables)
        self.assertIsNone(updated)
        self.assertIsNone(err)

    def test_script_log_captured(self):
        script = "pypost.log('hello'); pypost.log('world')"
        _, logs, err = ScriptExecutor.execute(script, self._req(), self._resp(), {})
        self.assertEqual(logs, ["hello", "world"])
        self.assertIsNone(err)

    def test_stdout_captured_and_appended_to_logs(self):
        script = "print('from stdout')"
        _, logs, err = ScriptExecutor.execute(script, self._req(), self._resp(), {})
        self.assertTrue(any("[STDOUT]" in l for l in logs))
        self.assertIsNone(err)

    def test_script_error_returns_traceback(self):
        script = "raise ValueError('oops')"
        updated, logs, err = ScriptExecutor.execute(script, self._req(), self._resp(), {})
        self.assertIsNone(updated)
        self.assertIsNotNone(err)
        self.assertIn("ValueError", err)
        self.assertIn("oops", err)

    def test_request_and_response_available_in_script(self):
        script = "pypost.set('method', request.method); pypost.set('status', str(response.status_code))"
        updated, _, err = ScriptExecutor.execute(script, self._req(), self._resp(201), {})
        self.assertIsNone(err)
        self.assertEqual(updated["method"], "GET")
        self.assertEqual(updated["status"], "201")

    def test_original_variables_not_mutated(self):
        script = "pypost.set('new_key', 'new_val')"
        original = {"existing": "val"}
        ScriptExecutor.execute(script, self._req(), self._resp(), original)
        self.assertNotIn("new_key", original)


if __name__ == "__main__":
    unittest.main()
