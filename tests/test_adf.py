"""Red repro tests for PYPOST-1283: `to_adf` plain-text -> Atlassian Document Format.

`20-architecture.md` plans a new `pypost/core/adf.py` module exposing
`to_adf(text: str) -> str`, a pure function converting plain text into a
JSON-serialized ADF v1 document so neither a GUI user nor an agent has to
hand-write Jira's rich-text structure. The module does not exist yet, so
these tests fail today with `ModuleNotFoundError` — the intended "missing
feature" reason, not a broken fixture.
"""
from __future__ import annotations

import json
import unittest

import pytest

pytestmark = pytest.mark.timeout(30)


class TestToAdf(unittest.TestCase):
    def test_single_line_text_produces_one_paragraph_one_text_node(self) -> None:
        from pypost.core.adf import to_adf

        doc = json.loads(to_adf("Hello world"))

        self.assertEqual(doc["version"], 1)
        self.assertEqual(doc["type"], "doc")
        self.assertEqual(len(doc["content"]), 1)
        paragraph = doc["content"][0]
        self.assertEqual(paragraph["type"], "paragraph")
        self.assertEqual(len(paragraph["content"]), 1)
        text_node = paragraph["content"][0]
        self.assertEqual(text_node["type"], "text")
        self.assertEqual(text_node["text"], "Hello world")

    def test_blank_line_separated_text_produces_multiple_paragraphs(self) -> None:
        from pypost.core.adf import to_adf

        doc = json.loads(to_adf("First paragraph.\n\nSecond paragraph."))

        self.assertEqual(len(doc["content"]), 2)
        self.assertEqual(
            doc["content"][0]["content"][0]["text"], "First paragraph."
        )
        self.assertEqual(
            doc["content"][1]["content"][0]["text"], "Second paragraph."
        )
        for paragraph in doc["content"]:
            self.assertEqual(paragraph["type"], "paragraph")

    def test_empty_string_produces_valid_doc_with_empty_paragraph(self) -> None:
        from pypost.core.adf import to_adf

        doc = json.loads(to_adf(""))

        self.assertEqual(doc["version"], 1)
        self.assertEqual(doc["type"], "doc")
        self.assertEqual(doc["content"], [{"type": "paragraph", "content": []}])


if __name__ == "__main__":
    unittest.main()
