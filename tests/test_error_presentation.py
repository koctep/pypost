"""Tests for what a failed request says to the user."""
import unittest

from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.ui.presenters.error_presentation import describe


def _error(category, message="failed", detail=None):
    return ExecutionError(category=category, message=message, detail=detail)


class DescribeTests(unittest.TestCase):
    def test_cancellation_says_nothing(self):
        self.assertIsNone(
            describe(_error(ErrorCategory.CANCELLED, "Request cancelled"))
        )

    def test_network_names_the_url_and_hides_the_raw_detail(self):
        raw = "HTTPSConnectionPool(host='secret', port=443): Max retries exceeded"
        prompt = describe(_error(ErrorCategory.NETWORK, detail=raw), "http://x")

        self.assertEqual("Request Error", prompt.title)
        self.assertIn("http://x", prompt.message)
        self.assertNotIn(raw, prompt.message)

    def test_timeout_names_the_url(self):
        prompt = describe(_error(ErrorCategory.TIMEOUT), "http://slow")

        self.assertIn("http://slow", prompt.message)
        self.assertIn("timed out", prompt.message)

    def test_template_and_script_errors_carry_the_detail(self):
        for category in (ErrorCategory.TEMPLATE, ErrorCategory.SCRIPT):
            with self.subTest(category=category):
                prompt = describe(_error(category, detail="line 3"))
                self.assertIn("line 3", prompt.message)

    def test_detail_falls_back_to_the_message(self):
        prompt = describe(_error(ErrorCategory.UNKNOWN, message="boom", detail=None))

        self.assertIn("boom", prompt.message)

    def test_an_unmapped_category_uses_the_unknown_wording(self):
        prompt = describe(_error(ErrorCategory.HISTORY, detail="disk full"))

        self.assertIn("disk full", prompt.message)

    def test_an_error_that_merely_mentions_aborting_is_still_reported(self):
        """Cancellation is a category, not a word to look for in the detail."""
        prompt = describe(
            _error(ErrorCategory.UNKNOWN, detail="Connection aborted by peer")
        )

        self.assertIsNotNone(prompt)

    def test_a_bare_cancellation_string_still_says_nothing(self):
        """Older paths reported cancellation as a plain string."""
        self.assertIsNone(describe("request cancelled"))
        self.assertIsNone(describe("request aborted by user"))

    def test_a_bare_error_string_is_reported(self):
        prompt = describe("socket closed")

        self.assertEqual("Error", prompt.title)
        self.assertIn("socket closed", prompt.message)


if __name__ == "__main__":
    unittest.main()
