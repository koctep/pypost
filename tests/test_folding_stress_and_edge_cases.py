"""Stress and edge-case payload test suite for code folding (PYPOST-1371).

Asserts contract and behavior for:
- Truncated and malformed payloads (JSON, XML, YAML) gracefully returning []
- Deeply nested structures (100-200+ levels) without unhandled RecursionError escaping
- Oversized payloads (>10 MB) background worker dispatch and completion
- High-frequency rapid burst edits, debounce cancellation, and worker cleanup
"""

from __future__ import annotations

import json
import logging
from typing import Any

import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QPlainTextEdit

from pypost.ui.widgets.fold import BodyFormat, FoldController
from pypost.ui.widgets.fold.fold_worker import FoldScanWorker
from pypost.ui.widgets.fold.structure_scanner import scan_text
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(30)


# ============================================================================
# Synthetic Payload Generators
# ============================================================================

def generate_truncated_payload(
    body_format: BodyFormat, sample_text: str, cut_ratio: float = 0.5
) -> str:
    """Return payload truncated at cut_ratio of length."""
    cut_len = max(1, int(len(sample_text) * cut_ratio))
    return sample_text[:cut_len]


def generate_deep_json(depth: int = 200) -> str:
    """Generate deeply nested JSON array structure."""
    return ("[" * depth) + "1" + ("]" * depth)


def generate_deep_xml(depth: int = 200) -> str:
    """Generate deeply nested XML element hierarchy."""
    open_tags = "".join(f"<n{i}>" for i in range(depth))
    close_tags = "".join(f"</n{i}>" for i in reversed(range(depth)))
    return f"<root>{open_tags}leaf{close_tags}</root>"


def generate_deep_yaml(depth: int = 200) -> str:
    """Generate deeply nested YAML mapping hierarchy with indentation."""
    lines = []
    for i in range(depth):
        lines.append(f"{'  ' * i}k{i}:")
    lines.append(f"{'  ' * depth}value")
    return "\n".join(lines)


def generate_oversized_json(target_bytes: int = 10 * 1024 * 1024 + 1024) -> str:
    """Generate synthetic JSON document exceeding target_bytes (~10 MB)."""
    chunk_size = 200_000
    num_chunks = (target_bytes // chunk_size) + 1
    chunk_str = "x" * chunk_size
    items = [f'{{"id": {i}, "data": "{chunk_str}"}}' for i in range(num_chunks)]
    return '{"items": [\n' + ",\n".join(items) + "\n]}"


# ============================================================================
# Category A: Truncated & Malformed Payloads
# ============================================================================

class TestTruncatedAndMalformedPayloads:
    """Category A: Scanners must gracefully handle truncated / malformed inputs."""

    def test_truncated_json_returns_empty_regions(self) -> None:
        """Truncated JSON (cut braces, dangling keys) must return empty list."""
        sample = json.dumps(
            {"users": [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]}
        )
        for ratio in [0.2, 0.4, 0.6, 0.8]:
            truncated = generate_truncated_payload(BodyFormat.JSON, sample, cut_ratio=ratio)
            regions = scan_text(truncated, BodyFormat.JSON)
            assert regions == [], f"Expected empty regions for truncated JSON at ratio {ratio}"

    def test_malformed_json_returns_empty_regions(self) -> None:
        """Malformed JSON (unclosed strings, invalid tokens) must return empty list."""
        malformed_cases = [
            '{"unclosed_string": "value',
            '{"key":: "double_colon"}',
            '{"trailing_comma": [1, 2, ],}',
            '{not_quoted_key: 123}',
            '{"open_brace": {',
            '<<<not json>>>',
        ]
        for case in malformed_cases:
            regions = scan_text(case, BodyFormat.JSON)
            assert regions == [], f"Expected empty regions for malformed JSON: {case!r}"

    def test_truncated_xml_returns_empty_regions(self) -> None:
        """Truncated XML (cut tags, cut attributes, cut CDATA) must return empty list."""
        sample = (
            '<root><item id="123"><name>Alpha</name>'
            '<desc><![CDATA[Data block]]></desc></item></root>'
        )
        for ratio in [0.2, 0.4, 0.6, 0.8]:
            truncated = generate_truncated_payload(BodyFormat.XML, sample, cut_ratio=ratio)
            regions = scan_text(truncated, BodyFormat.XML)
            assert regions == [], f"Expected empty regions for truncated XML at ratio {ratio}"

    def test_malformed_xml_returns_empty_regions(self) -> None:
        """Malformed XML (mismatched tags, multiple roots, bad entity) must return empty list."""
        malformed_cases = [
            '<root><item></other></root>',
            '<root></root><second_root></second_root>',
            '<root>&invalid_entity;</root>',
            '<root><tag attr="unclosed_val></root>',
            '<![CDATA[ unclosed cdata',
            '<<<not xml>>>',
        ]
        for case in malformed_cases:
            regions = scan_text(case, BodyFormat.XML)
            assert regions == [], f"Expected empty regions for malformed XML: {case!r}"

    def test_truncated_yaml_returns_empty_regions(self) -> None:
        """Truncated YAML (unclosed flow sequence/mapping, unclosed quotes) returns empty list."""
        truncated_cases = [
            "items:\n  - [1, 2, ",
            "root:\n  mapping: {key: value, other: ",
            'key: "this is an unclosed quote that ends abruptly',
            "data: [unclosed bracket",
        ]
        for case in truncated_cases:
            regions = scan_text(case, BodyFormat.YAML)
            assert regions == [], f"Expected empty regions for truncated YAML: {case!r}"

    def test_malformed_yaml_returns_empty_regions(self) -> None:
        """Malformed YAML (tab indentation conflicts, bad scalar) must return empty list."""
        malformed_cases = [
            "items:\n\t- tab_indented: true\n  - space_indented: true",
            "key: 'unclosed single quote",
            'key: "unclosed double quote\nnext: 1',
            "key: : invalid colon syntax",
        ]
        for case in malformed_cases:
            regions = scan_text(case, BodyFormat.YAML)
            assert regions == [], f"Expected empty regions for malformed YAML: {case!r}"


# ============================================================================
# Category B: Deeply Nested Hierarchies (Failing Repro - Recursion Safety)
# ============================================================================

class TestDeeplyNestedRecursionSafety:
    """Category B: Scanners must handle deep recursion without unhandled RecursionError."""

    def test_deep_yaml_recursion_safety(self) -> None:
        """Deeply nested YAML (500 levels) naturally exceeds recursion limit in PyYAML parser."""
        payload = generate_deep_yaml(depth=500)
        # On unhardened scanner, this raises unhandled RecursionError escaping scan_text
        regions = scan_text(payload, BodyFormat.YAML)
        assert regions == [], "Deeply nested YAML exceeding recursion must return []"

    def test_deep_json_recursion_safety(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Deeply nested JSON recursion limit must not escape unhandled RecursionError."""
        payload = generate_deep_json(depth=200)

        def mock_loads(text: str) -> Any:
            raise RecursionError("maximum recursion depth exceeded while parsing JSON")

        monkeypatch.setattr("json.loads", mock_loads)
        # On unhardened scanner, this raises unhandled RecursionError escaping scan_text
        regions = scan_text(payload, BodyFormat.JSON)
        assert regions == [], "Deeply nested JSON exceeding recursion must return []"

    def test_deep_xml_recursion_safety(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Deeply nested XML recursion limit must not escape unhandled RecursionError."""
        payload = generate_deep_xml(depth=200)

        def mock_fromstring(text: str) -> Any:
            raise RecursionError("maximum recursion depth exceeded while parsing XML")

        monkeypatch.setattr("xml.etree.ElementTree.fromstring", mock_fromstring)
        # On unhardened scanner, this raises unhandled RecursionError escaping scan_text
        regions = scan_text(payload, BodyFormat.XML)
        assert regions == [], "Deeply nested XML exceeding recursion must return []"


# ============================================================================
# Category C: Extreme Payloads (>10 MB)
# ============================================================================

class TestOversizedPayloads:
    """Category C: Payloads > 10 MB must dispatch to FoldScanWorker and complete within timeout."""

    def test_oversized_payload_background_dispatch_and_completion(
        self, qapp: QApplication
    ) -> None:
        """Synthetic payload > 10 MB must trigger FoldScanWorker and complete cleanly."""
        target_size = 10 * 1024 * 1024 + 1024
        payload = generate_oversized_json(target_size)
        assert len(payload) > 10 * 1024 * 1024, "Payload must exceed 10 MB"

        editor = QPlainTextEdit()
        fc = FoldController(editor, body_format=BodyFormat.JSON)
        editor.setPlainText(payload)

        spy = QSignalSpy(fc.scan_finished)
        fc.ensure_scanned()

        active_worker = getattr(fc, "_active_worker", None)
        assert active_worker is not None, "Oversized document must spawn a background worker"
        assert isinstance(active_worker, FoldScanWorker)

        # Worker must finish and emit scan_finished within explicit timeout
        process_until(lambda: spy.count() >= 1, timeout_ms=25_000)
        assert spy.count() >= 1, "scan_finished must be emitted for oversized document"
        assert getattr(fc, "_active_worker", None) is None, "Worker reference must be cleared"
        assert len(fc.regions()) > 0, "Fold regions must be populated for oversized document"


# ============================================================================
# Category D: High-Frequency Rapid Edits and Debounce
# ============================================================================

class TestRapidEditsAndDebounce:
    """Category D: Rapid burst edits, debounce cancellation, and worker cleanup."""

    def test_rapid_burst_edits_debouncing_and_worker_cleanup(
        self, qapp: QApplication
    ) -> None:
        """Rapid document edits must be debounced and cleanly terminate workers without leaks."""
        editor = QPlainTextEdit()
        fc = FoldController(editor, body_format=BodyFormat.JSON)
        spy = QSignalSpy(fc.scan_finished)

        # Trigger several edits in quick succession (simulating burst typing)
        for i in range(5):
            editor.setPlainText(f'{{"burst_index": {i}, "nested": {{"id": {i}}}}}')

        # Allow debounce timer (200 ms) to fire and complete scan
        process_until(lambda: spy.count() >= 1, timeout_ms=5_000)
        assert spy.count() >= 1, "Final debounced scan must complete and emit scan_finished"
        assert len(FoldScanWorker._LIVE_WORKERS) == 0, "No workers must leak in _LIVE_WORKERS"


# ============================================================================
# Category E: Observability & Structured Warning Logging
# ============================================================================

class TestObservabilityAndStructuredLogging:
    """Category E: Verify structured warning logs for malformed/truncated and stress inputs."""

    def test_json_parse_skip_logs_error_type_and_length_without_payload_leak(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Malformed JSON must log warning with error_type and length without payload leakage."""
        secret_content = "super_secret_user_token_payload_xyz_123"
        malformed_json = f'{{"secret": "{secret_content}", "broken": ['
        with caplog.at_level(logging.WARNING):
            regions = scan_text(malformed_json, BodyFormat.JSON)

        assert regions == []
        json_warns = [
            r for r in caplog.records
            if "json_scan_parse_skipped" in r.getMessage() and r.levelno == logging.WARNING
        ]
        assert len(json_warns) == 1
        msg = json_warns[0].getMessage()
        assert "error_type=JSONDecodeError" in msg
        assert f"length={len(malformed_json)}" in msg
        assert secret_content not in msg

    def test_yaml_parse_skip_logs_error_type_and_length_without_payload_leak(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Malformed YAML must log warning with error_type and length without payload leakage."""
        secret_content = "secret_yaml_api_key_never_leak_456"
        malformed_yaml = f"items:\n\t- secret: {secret_content}\n  - invalid"
        with caplog.at_level(logging.WARNING):
            regions = scan_text(malformed_yaml, BodyFormat.YAML)

        assert regions == []
        yaml_warns = [
            r for r in caplog.records
            if "yaml_scan_parse_skipped" in r.getMessage() and r.levelno == logging.WARNING
        ]
        assert len(yaml_warns) == 1
        msg = yaml_warns[0].getMessage()
        assert "error_type=" in msg
        assert f"length={len(malformed_yaml)}" in msg
        assert secret_content not in msg

    def test_xml_parse_skip_logs_error_type_and_length_without_payload_leak(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Malformed XML must log warning with error_type and length without payload leakage."""
        secret_content = "secret_xml_password_hash_789"
        malformed_xml = f"<root><auth>{secret_content}</auth><broken>"
        with caplog.at_level(logging.WARNING):
            regions = scan_text(malformed_xml, BodyFormat.XML)

        assert regions == []
        xml_warns = [
            r for r in caplog.records
            if "xml_scan_parse_skipped" in r.getMessage() and r.levelno == logging.WARNING
        ]
        assert len(xml_warns) == 1
        msg = xml_warns[0].getMessage()
        assert "error_type=ParseError" in msg
        assert f"length={len(malformed_xml)}" in msg
        assert secret_content not in msg

    def test_stress_recursion_error_logging_structured_attributes(
        self, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Recursion errors under stress must log structured error_type and length."""
        secret_marker = "sensitive_stress_marker_999"
        payload = f'{{"depth": "{secret_marker}"}}'

        def mock_loads(text: str) -> Any:
            raise RecursionError("maximum recursion depth exceeded")

        monkeypatch.setattr("json.loads", mock_loads)
        with caplog.at_level(logging.WARNING):
            regions = scan_text(payload, BodyFormat.JSON)

        assert regions == []
        warns = [
            r for r in caplog.records
            if "json_scan_parse_skipped" in r.getMessage() and r.levelno == logging.WARNING
        ]
        assert len(warns) == 1
        msg = warns[0].getMessage()
        assert "error_type=RecursionError" in msg
        assert f"length={len(payload)}" in msg
        assert secret_marker not in msg
