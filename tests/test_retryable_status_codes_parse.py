"""Unit tests for parse_retryable_status_codes (PYPOST-423)."""

import unittest

from pypost.models.retry import (
    RetryableCodesValidationFailure,
    parse_retryable_status_codes,
)


class TestParseRetryableStatusCodes(unittest.TestCase):
    def test_empty_and_whitespace_returns_empty_list(self):
        self.assertEqual(parse_retryable_status_codes(""), [])
        self.assertEqual(parse_retryable_status_codes("   "), [])
        self.assertEqual(parse_retryable_status_codes("\t\n"), [])

    def test_valid_single_and_multiple(self):
        self.assertEqual(parse_retryable_status_codes("500"), [500])
        self.assertEqual(parse_retryable_status_codes("429,500,503"), [429, 500, 503])

    def test_whitespace_around_commas(self):
        self.assertEqual(
            parse_retryable_status_codes("429, 500 , 503"),
            [429, 500, 503],
        )

    def test_empty_segment_fails(self):
        r = parse_retryable_status_codes("500,")
        self.assertIsInstance(r, RetryableCodesValidationFailure)
        self.assertEqual(r.reason, "empty_segment")

        r2 = parse_retryable_status_codes(",500")
        self.assertIsInstance(r2, RetryableCodesValidationFailure)
        self.assertEqual(r2.reason, "empty_segment")

        r3 = parse_retryable_status_codes("500,,503")
        self.assertIsInstance(r3, RetryableCodesValidationFailure)
        self.assertEqual(r3.reason, "empty_segment")

    def test_invalid_token(self):
        r = parse_retryable_status_codes("500,abc")
        self.assertIsInstance(r, RetryableCodesValidationFailure)
        self.assertEqual(r.reason, "invalid_token")

    def test_out_of_range(self):
        r = parse_retryable_status_codes("99")
        self.assertIsInstance(r, RetryableCodesValidationFailure)
        self.assertEqual(r.reason, "out_of_range")

        r2 = parse_retryable_status_codes("600")
        self.assertIsInstance(r2, RetryableCodesValidationFailure)
        self.assertEqual(r2.reason, "out_of_range")

    def test_unsupported_separator_yields_invalid_token(self):
        r = parse_retryable_status_codes("500;501")
        self.assertIsInstance(r, RetryableCodesValidationFailure)
        self.assertEqual(r.reason, "invalid_token")

    def test_non_empty_raw_all_invalid_tokens(self):
        r = parse_retryable_status_codes("foo,bar")
        self.assertIsInstance(r, RetryableCodesValidationFailure)
        self.assertEqual(r.reason, "invalid_token")


if __name__ == "__main__":
    unittest.main()
