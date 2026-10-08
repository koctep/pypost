"""Differential compatibility and callback isolation for cooperative decoding."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import sys
import threading
from typing import Any

import pytest
import yaml

from pypost.core.collection_import import (
    CollectionImportFileError, _read_records, load_collection_import_candidates,
)
from pypost.core.collection_import_decode import _JSONParser, _yaml_decode, read_import_document
from pypost.core.qt.collection_import_parse_worker import CollectionImportCancelled

pytestmark = pytest.mark.timeout(30)


def _noop() -> None:
    pass


@pytest.mark.parametrize('depth', [600, 900])
@pytest.mark.parametrize('shape', ['array', 'object', 'mixed'])
def test_json_deep_nesting_matches_standard_decoder(shape: str, depth: int) -> None:
    text = '0'
    for index in range(depth):
        text = ('[' + text + ']' if shape == 'array' or (shape == 'mixed' and index % 2)
                else '{"child":' + text + '}')
    expected = json.loads(text)
    actual = _JSONParser(_noop).decode(text)
    # Walk explicitly: recursive equality itself can exceed Python's frame budget.
    for _ in range(depth):
        assert type(actual) is type(expected)
        actual = actual[0] if isinstance(actual, list) else actual['child']
        expected = expected[0] if isinstance(expected, list) else expected['child']
    assert actual == expected == 0


@pytest.mark.parametrize('shape', ['array', 'object'])
def test_reader_accepts_deep_ignored_json_field(tmp_path: Path, shape: str) -> None:
    path = tmp_path / 'deep.json'
    opening, closing = ('[', ']') if shape == 'array' else ('{"child":', '}')
    path.write_text('{"name":"deep","ignored":' + opening * 600 + '0' +
                    closing * 600 + '}', encoding='utf-8')
    assert json.loads(path.read_text())['name'] == 'deep'
    candidates, errors = load_collection_import_candidates(path, on_progress=lambda *_: None)
    assert [candidate.name for candidate in candidates] == ['deep']
    assert errors == []


@pytest.mark.parametrize('invalid', ['[1,]', '{"a":1,}', '{"a" 0}', '"\\q"', '1e+'])
def test_deep_json_syntax_errors_match_standard_decoder(invalid: str) -> None:
    text = '[{"child":' * 300 + invalid + '}]' * 300
    with pytest.raises(json.JSONDecodeError) as expected:
        json.loads(text)
    with pytest.raises(json.JSONDecodeError) as actual:
        _JSONParser(_noop).decode(text)
    assert (actual.value.msg, actual.value.pos) == (expected.value.msg, expected.value.pos)


def test_excessive_json_nesting_remains_cancellable() -> None:
    cancelled = CollectionImportCancelled('deep nesting')
    calls = 0

    def checkpoint() -> None:
        nonlocal calls
        calls += 1
        if calls == 5000:
            raise cancelled

    with pytest.raises(CollectionImportCancelled) as actual:
        _JSONParser(checkpoint).decode('[' * 10000 + '0' + ']' * 10000)
    assert actual.value is cancelled
    assert calls == 5000


def test_excessive_incomplete_json_nesting_terminates() -> None:
    text = '[' * 10000
    with pytest.raises(json.JSONDecodeError) as actual:
        _JSONParser(_noop).decode(text)
    assert actual.value.pos == len(text)


@pytest.mark.parametrize('text', [
    '{}', '[]', '[true,false,null,0,-0,-0.0,1e+30,1.25E-3]',
    '{"duplicate":1,"duplicate":2,"nested":[{},["test"]]}',
    '"\\ud83d\\ude00\\ud800\\udfff\\n\\t\\b\\f\\r\\/\\\\\\\""',
    '"' + 'x' * 4094 + '\\u1234' + 'y' * 5000 + '"',
    '{"' + 'k' * 10000 + '":"' + 'v' * 10000 + '"}',
    ' ' * 10000 + '[1,2]' + '\n' * 10000,
    '1' + '0' * 10000 + '.0', '1e' + '0' * 10000 + '1',
    'Infinity', '-Infinity', 'NaN', '"Unicode: \u263a"',
])
def test_json_matches_standard_decoder(text: str) -> None:
    expected = json.loads(text)
    actual = _JSONParser(_noop).decode(text)
    if isinstance(expected, float) and math.isnan(expected):
        assert math.isnan(actual)
    else:
        assert actual == expected
        assert type(actual) is type(expected)
    if text == '-0.0':
        assert math.copysign(1, actual) == -1


@pytest.mark.parametrize('text', [
    '', ' ', '[', '{', '{"a" 1}', '{"a":}', '{a:1}', '[1,]', '{"a":1,}',
    '"unterminated', '"line\nbreak"', '"\\x"', '"\\u12xz"',
    '01', '-01', '1.', '1e+', '[1 2]', '{} trailing', 'true false',
    '"' + 'x' * 4095 + '\\uZZZZ"',
])
def test_json_syntax_positions_match_standard_decoder(text: str) -> None:
    with pytest.raises(json.JSONDecodeError) as expected:
        json.loads(text)
    with pytest.raises(json.JSONDecodeError) as actual:
        _JSONParser(_noop).decode(text)
    assert actual.value.pos == expected.value.pos


def test_json_integer_limit_is_preserved() -> None:
    text = '1' * (sys.get_int_max_str_digits() + 1)
    if not sys.get_int_max_str_digits():
        pytest.skip('interpreter integer digit restriction disabled')
    with pytest.raises(ValueError):
        json.loads(text)
    with pytest.raises(ValueError):
        _JSONParser(_noop).decode(text)


@pytest.mark.parametrize('text', [
    'name: plain\nvalue: abc', 'value: "escaped\\n\\u263a"', "value: 'one''two'",
    'value: |\n  one\n  two\n', 'value: >\n  one\n  two\n',
    'name: Unicode\r\nvalue: \u263a\r\n', 'value: !!int 12\nflag: true\nnone: null',
    'date: 2026-10-08\ntime: 2026-10-08T12:30:00Z',
    'name: first\nname: second', 'a: &a {x: 1}\nb: {<<: *a, y: 2}',
    'a: &a [1,2]\nb: *a', 'value: !!binary aGVsbG8=',
])
def test_yaml_matches_safe_loader(text: str) -> None:
    assert _yaml_decode(text, _noop) == yaml.safe_load(text)


@pytest.mark.parametrize('text', [
    'name: [', '---\na: 1\n---\nb: 2', 'value: !!python/object:builtins.object {}',
    'value: !!int bad', 'value: !!timestamp 2026-99-99',
    'value: !!bool maybe', 'value: "bad\\q"', 'value: \x01',
])
def test_yaml_error_type_matches_safe_loader(text: str) -> None:
    with pytest.raises(Exception) as expected:
        yaml.safe_load(text)
    with pytest.raises(type(expected.value)):
        _yaml_decode(text, _noop)


def test_yaml_alias_identity_and_recursive_nodes() -> None:
    actual = _yaml_decode('a: &a [*a]\nb: *a', _noop)
    assert actual['a'] is actual['b']
    assert actual['a'][0] is actual['a']


@pytest.mark.parametrize('text', [
    'a: &a {x: 1, y: 1}\nb: &b {x: 2, z: 2}\nc: {<<: [*a, *b], y: 3}',
    'a: &a {x: 1}\nb: &b {<<: *a, y: 2}\nc: {<<: [*a, *b]}',
    'a: &a {x: 1}\nb: {<<: *a, <<: {x: 2}, x: 3}',
    'a: {=: value}',
])
def test_yaml_merge_order_matches_safe_loader(text: str) -> None:
    assert _yaml_decode(text, _noop) == yaml.safe_load(text)


def test_yaml_merge_preserves_recursive_alias_identity() -> None:
    actual = _yaml_decode('base: &b {self: *b}\nmerged: {<<: *b}', _noop)
    assert actual['base']['self'] is actual['base']
    assert actual['merged']['self'] is actual['base']


@pytest.mark.parametrize('text', ['a: {<<: 1}', 'a: {<<: [{x: 1}, 2]}'])
def test_yaml_merge_errors_match_safe_loader(text: str) -> None:
    with pytest.raises(yaml.constructor.ConstructorError) as expected:
        yaml.safe_load(text)
    with pytest.raises(yaml.constructor.ConstructorError) as actual:
        _yaml_decode(text, _noop)
    assert str(actual.value) == str(expected.value)


@pytest.mark.parametrize('shape', ['sequence', 'mapping'])
def test_yaml_cancels_during_merge_sequence_assembly(shape: str) -> None:
    from pypost.core.collection_import_decode import _SafeLoader

    count = 20000
    # Compose first so the cancellation cannot be satisfied during scanning or
    # flattening the source mappings. Exercise both repeated aliases and a large
    # individual source mapping, which requires bounded extend operations.
    text = ('base: &b {key: value}\nmerged: {<<: [' + ','.join(['*b'] * count) + ']}'
            if shape == 'sequence' else
            'base: &b {' + ','.join(f'k{index}: value' for index in range(count)) +
            '}\nmerged: {<<: *b}')
    node = yaml.compose(text, Loader=yaml.SafeLoader)
    target = node.value[1][1]
    cancelled = CollectionImportCancelled('merge assembly')
    assembled: list[int] = []

    def checkpoint() -> None:
        frame = sys._getframe(1)
        while frame is not None:
            if frame.f_code.co_name == 'flatten_mapping':
                merge = frame.f_locals.get('merge', [])
                if 0 < len(merge) < count:
                    assembled.append(len(merge))
                    raise cancelled
            frame = frame.f_back

    loader = _SafeLoader('', checkpoint)
    try:
        with pytest.raises(CollectionImportCancelled) as actual:
            loader.flatten_mapping(target)
        assert actual.value is cancelled
        assert assembled and 0 < assembled[0] < count
    finally:
        loader.dispose()


@pytest.mark.parametrize('suffix', ['.json', '.yaml'])
@pytest.mark.parametrize('value', ['!!timestamp 2026-99-99', '!!int bad', '!!bool maybe'])
def test_fallback_retains_original_json_error(
    tmp_path: Path, suffix: str, value: str,
) -> None:
    path = tmp_path / ('invalid' + suffix)
    text = 'name: test\nvalue: ' + value
    path.write_text(text, encoding='utf-8')
    if suffix == '.json':
        with pytest.raises(json.JSONDecodeError) as expected:
            json.loads(text)
        with pytest.raises(CollectionImportFileError) as actual:
            _read_records(path, _noop)
        assert str(expected.value) in str(actual.value)
    else:
        with pytest.raises(Exception) as expected:
            yaml.safe_load(text)
        with pytest.raises(type(expected.value)):
            _read_records(path, _noop)


@pytest.mark.parametrize('phase', [
    'reading', 'json', 'yaml', 'fallback', 'yaml_init', 'yaml_construct', 'yaml_merge',
])
@pytest.mark.parametrize('error_type', [
    ValueError, OSError, yaml.YAMLError, CollectionImportCancelled,
])
def test_callback_failure_identity_and_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str, error_type: type[Exception],
) -> None:
    from pypost.core import collection_import_decode as decode

    path = tmp_path / ('input.yaml' if phase.startswith('yaml') else 'input.json')
    text = ('{"name":"' + 'x' * 20000 + '"}' if phase in ('reading', 'json')
            else 'name: ' + 'x' * 20000)
    if phase == 'yaml_merge':
        text = 'a: &a {x: 1}\nb: {<<: *a, y: 2}'
    path.write_text(text, encoding='utf-8')
    original = error_type('callback sentinel')
    disposed: list[bool] = []
    real_dispose = decode._SafeLoader.dispose

    def dispose(loader: Any) -> None:
        disposed.append(True)
        real_dispose(loader)

    monkeypatch.setattr(decode._SafeLoader, 'dispose', dispose)

    def checkpoint() -> None:
        frame = sys._getframe(1)
        names: set[str] = set()
        while frame is not None:
            names.add(frame.f_code.co_name)
            frame = frame.f_back
        target = {'reading': '_read_text', 'json': 'string',
                  'yaml': 'scan_plain', 'fallback': 'scan_plain', 'yaml_init': 'check_printable',
                  'yaml_construct': 'construct_object', 'yaml_merge': 'flatten_mapping'}[phase]
        if target in names:
            raise original

    with pytest.raises(error_type) as actual:
        _read_records(path, checkpoint)
    assert actual.value is original
    assert disposed == ([True] if (phase.startswith('yaml') or phase == 'fallback') else [])
    # A closed handle is also exercised by the real-file cancellation tests.
    path.unlink()


@pytest.mark.parametrize('format_name', ['json', 'yaml'])
def test_simultaneous_decoders_do_not_share_cancellation_state(format_name: str) -> None:
    barrier = threading.Barrier(2)
    cancelled = ValueError('cancel one import')
    scanstring = json.decoder.scanstring
    scanner = json.scanner.make_scanner

    def decode(cancel: bool) -> Any:
        first = True

        def checkpoint() -> None:
            nonlocal first
            if first:
                first = False
                barrier.wait(timeout=5)
                if cancel:
                    raise cancelled

        if format_name == 'json':
            return _JSONParser(checkpoint).decode('{"name":"' + 'x' * 10000 + '"}')
        return _yaml_decode('name: ' + 'x' * 10000, checkpoint)

    with ThreadPoolExecutor(max_workers=2) as pool:
        failed = pool.submit(decode, True)
        succeeded = pool.submit(decode, False)
        with pytest.raises(ValueError) as actual:
            failed.result(timeout=10)
        assert actual.value is cancelled
        assert succeeded.result(timeout=10) == {'name': 'x' * 10000}
    assert json.decoder.scanstring is scanstring
    assert json.scanner.make_scanner is scanner


@pytest.mark.parametrize('suffix', ['.json', '.yaml', '.unknown'])
def test_successful_reader_keeps_record_progress_and_newline_semantics(
    tmp_path: Path, suffix: str,
) -> None:
    path = tmp_path / ('input' + suffix)
    text = ('[{"name":"one"},{"name":"two"}]' if suffix == '.json'
            else '- name: one\r\n- name: two\r\n')
    path.write_text(text, encoding='utf-8')
    progress: list[tuple[int, int]] = []
    candidates, errors = load_collection_import_candidates(
        path, on_progress=lambda done, total: progress.append((done, total)))
    assert [item.name for item in candidates] == ['one', 'two']
    assert errors == []
    assert (0, 0) in progress
    assert [item for item in progress if item != (0, 0)] == [(1, 2), (2, 2)]
    assert read_import_document(path) == read_import_document(path, _noop)
