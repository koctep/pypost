"""Direct tests for PasteJsonFormatWorker (PYPOST-724)."""

from __future__ import annotations

import json
import unittest

import pytest

from pypost.ui.widgets.fold import BodyFormat
from pypost.ui.widgets.paste_json_worker import PasteJsonFormatWorker

pytestmark = pytest.mark.timeout(30)


class TestPasteJsonFormatWorker(unittest.TestCase):
    def _run_worker(
        self,
        *,
        text: str,
        body_format: BodyFormat,
        yaml_as_json: bool,
        generation_id: int = 42,
        indent_size: int = 2,
    ) -> list[tuple[int, str | None]]:
        received: list[tuple[int, str | None]] = []
        worker = PasteJsonFormatWorker(
            generation_id,
            text,
            indent_size=indent_size,
            body_format=body_format,
            yaml_as_json=yaml_as_json,
        )
        worker.finished_with_result.connect(
            lambda gen, result: received.append((gen, result))
        )
        worker.run()
        return received

    def test_valid_json_formats_with_indent(self) -> None:
        received = self._run_worker(
            text='{"a":1}',
            body_format=BodyFormat.JSON,
            yaml_as_json=False,
            indent_size=4,
        )
        self.assertEqual(received, [(42, '{\n    "a": 1\n}')])

    def test_valid_json_converts_to_yaml_when_yaml_as_json(self) -> None:
        received = self._run_worker(
            text='{"name":"demo"}',
            body_format=BodyFormat.YAML,
            yaml_as_json=True,
        )
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][0], 42)
        self.assertIn("name: demo", received[0][1] or "")

    def test_valid_json_stays_json_when_yaml_format_without_flag(self) -> None:
        received = self._run_worker(
            text='{"a":1}',
            body_format=BodyFormat.YAML,
            yaml_as_json=False,
        )
        self.assertEqual(received[0][1], json.dumps({"a": 1}, indent=2))

    def test_invalid_json_emits_none(self) -> None:
        received = self._run_worker(
            text="{not json",
            body_format=BodyFormat.JSON,
            yaml_as_json=False,
        )
        self.assertEqual(received, [(42, None)])

    def test_generation_id_passthrough(self) -> None:
        received = self._run_worker(
            text='{"ok":true}',
            body_format=BodyFormat.JSON,
            yaml_as_json=False,
            generation_id=99,
        )
        self.assertEqual(received[0][0], 99)
