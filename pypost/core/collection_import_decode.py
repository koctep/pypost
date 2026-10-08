"""Cooperative, instance-local decoding for collection imports.

String escape handling and object grammar adapt CPython's json.decoder
(Copyright (c) 2001-2024 Python Software Foundation; All Rights Reserved).
PSF License Version 2 is retained below.
Adaptations bound lexical scans, use an iterative container stack, and inject
checkpoints without consuming Python recursion frames per container.

Merge flattening adapts PyYAML's SafeConstructor, preserving its node and alias
semantics while bounding merge-list assembly. PyYAML's MIT license follows:

Copyright (c) 2017-2021 Ingy döt Net
Copyright (c) 2006-2016 Kirill Simonov

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
--------------------------------------------

1. This LICENSE AGREEMENT is between the Python Software Foundation
("PSF"), and the Individual or Organization ("Licensee") accessing and
otherwise using this software ("Python") in source or binary form and
its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
analyze, test, perform and/or display publicly, prepare derivative works,
distribute, and otherwise use Python alone or in any derivative version,
provided, however, that PSF's License Agreement and PSF's notice of copyright,
i.e., "Copyright (c) 2001-2024 Python Software Foundation; All Rights Reserved"
are retained in Python alone or in any derivative version prepared by Licensee.

3. In the event Licensee prepares a derivative work that is based on
or incorporates Python or any part thereof, and wants to make
the derivative work available to others as provided herein, then
Licensee hereby agrees to include in any such work a brief summary of
the changes made to Python.

4. PSF is making Python available to Licensee on an "AS IS"
basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
INFRINGE ANY THIRD PARTY RIGHTS.

5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

6. This License Agreement will automatically terminate upon a material
breach of its terms and conditions.

7. Nothing in this License Agreement shall be deemed to create any
relationship of agency, partnership, or joint venture between PSF and
Licensee.  This License Agreement does not grant permission to use PSF
trademarks or trade name in a trademark sense to endorse or promote
products or services of Licensee, or any third party.

8. By copying, installing or otherwise using Python, Licensee
agrees to be bound by the terms and conditions of this License
Agreement.
"""
from __future__ import annotations

from collections.abc import Callable
import json
from json.decoder import (  # type: ignore[attr-defined]
    BACKSLASH, WHITESPACE, _decode_uXXXX,
)
from pathlib import Path
import re
import sys
from typing import Any, cast

import yaml

_WINDOW = 4096
_STRING_END = re.compile(r'["\\\x00-\x1f]')
_DIGITS = re.compile(r'[0-9]*')


class _CheckpointRaised(Exception):
    """Separate callback failures from parser and filesystem failures."""

    def __init__(self, original: Exception) -> None:
        self.original = original
        self.traceback = original.__traceback__


def protect_checkpoint(callback: Callable[[], None]) -> Callable[[], None]:
    def check() -> None:
        try:
            callback()
        except Exception as exc:
            raise _CheckpointRaised(exc) from exc
    return check


def _read_text(path: Path, check: Callable[[], None]) -> str:
    chunks: list[str] = []
    with path.open(encoding="utf-8") as stream:
        while True:
            check()
            chunk = stream.read(64 * 1024)
            check()
            if not chunk:
                break
            chunks.append(chunk)
    check()
    text = ''.join(chunks)
    check()
    return text


class _JSONParser:
    def __init__(self, check: Callable[[], None]) -> None:
        self.check = check

    def whitespace(self, text: str, pos: int) -> Any:
        while True:
            self.check()
            match = WHITESPACE.match(text, pos, pos + _WINDOW)
            assert match is not None
            end = match.end()
            if end - pos < _WINDOW:
                return match
            pos = end

    def string(self, text: str, end: int) -> tuple[str, int]:
        begin = end - 1
        pieces: list[str] = []
        while end < len(text):
            self.check()
            match = _STRING_END.search(text, end, end + _WINDOW)
            if match is None:
                pieces.append(text[end:end + _WINDOW])
                end += min(_WINDOW, len(text) - end)
                continue
            pieces.append(text[end:match.start()])
            end = match.end()
            terminator = match.group()
            if terminator == '"':
                self.check()
                result = ''.join(pieces)
                self.check()
                return result, end
            if terminator != '\\':
                raise json.JSONDecodeError('Invalid control character at', text, end - 1)
            if end >= len(text):
                break
            escape = text[end]
            if escape == 'u':
                code = _decode_uXXXX(text, end)
                end += 5
                if 0xD800 <= code <= 0xDBFF and text[end:end + 2] == '\\u':
                    second = _decode_uXXXX(text, end + 1)
                    if 0xDC00 <= second <= 0xDFFF:
                        code = 0x10000 + ((code - 0xD800) << 10) + second - 0xDC00
                        end += 6
                pieces.append(chr(code))
            else:
                if escape not in BACKSLASH:
                    raise json.JSONDecodeError('Invalid \\escape', text, end - 1)
                pieces.append(BACKSLASH[escape])
                end += 1
        raise json.JSONDecodeError('Unterminated string starting at', text, begin)

    def digits(self, text: str, pos: int) -> int:
        while True:
            self.check()
            match = _DIGITS.match(text, pos, pos + _WINDOW)
            assert match is not None
            end = match.end()
            if end - pos < _WINDOW:
                return end
            pos = end

    def number(self, text: str, pos: int) -> tuple[Any, int]:
        start = pos
        if text[pos:pos + 1] == '-':
            pos += 1
        if text[pos:pos + 1] == '0':
            pos += 1
        elif text[pos:pos + 1] in '123456789' and pos < len(text):
            pos = self.digits(text, pos)
        else:
            raise StopIteration(start)
        fractional = False
        if text[pos:pos + 1] == '.':
            end = self.digits(text, pos + 1)
            if end > pos + 1:
                pos = end
                fractional = True
        if text[pos:pos + 1] in ('e', 'E'):
            end = pos + 1
            if text[end:end + 1] in ('+', '-'):
                end += 1
            digits = self.digits(text, end)
            if digits > end:
                pos = digits
                fractional = True
        self.check()
        value = (float if fractional else int)(text[start:pos])
        self.check()
        return value, pos

    def object_key(self, text: str, pos: int) -> tuple[str, int]:
        if text[pos:pos + 1] != '"':
            raise json.JSONDecodeError(
                'Expecting property name enclosed in double quotes', text, pos)
        key, pos = self.string(text, pos + 1)
        pos = self.whitespace(text, pos).end()
        if text[pos:pos + 1] != ':':
            raise json.JSONDecodeError("Expecting ':' delimiter", text, pos)
        return key, self.whitespace(text, pos + 1).end()

    def scalar(self, text: str, pos: int) -> tuple[Any, int]:
        self.check()
        token = text[pos:pos + 1]
        if token == '"':
            return self.string(text, pos + 1)
        for literal, value in (('null', None), ('true', True), ('false', False),
                               ('NaN', float('nan')), ('Infinity', float('inf')),
                               ('-Infinity', float('-inf'))):
            if text.startswith(literal, pos):
                return value, pos + len(literal)
        if token in '-0123456789' and token:
            return self.number(text, pos)
        raise StopIteration(pos)

    def scan(self, text: str, pos: int) -> tuple[Any, int]:
        # Explicit frames preserve the C decoder's supported nesting without
        # multiplying Python frames or changing the process recursion limit.
        stack: list[tuple[Any, str | None]] = []
        while True:
            self.check()
            token = text[pos:pos + 1]
            if token in ('[', '{'):
                value: Any = [] if token == '[' else {}
                closing = ']' if token == '[' else '}'
                pos = self.whitespace(text, pos + 1).end()
                if text[pos:pos + 1] == closing:
                    pos += 1
                else:
                    key = None
                    if token == '{':
                        key, pos = self.object_key(text, pos)
                    stack.append((value, key))
                    continue
            else:
                try:
                    value, pos = self.scalar(text, pos)
                except StopIteration as exc:
                    raise json.JSONDecodeError('Expecting value', text, exc.value) from None
            while stack:
                self.check()
                container, key = stack[-1]
                if key is None:
                    container.append(value)
                else:
                    container[key] = value
                pos = self.whitespace(text, pos).end()
                closing = ']' if key is None else '}'
                token = text[pos:pos + 1]
                if token == closing:
                    stack.pop()
                    value = container
                    pos += 1
                    continue
                if token != ',':
                    raise json.JSONDecodeError("Expecting ',' delimiter", text, pos)
                comma = pos
                pos = self.whitespace(text, pos + 1).end()
                if text[pos:pos + 1] == closing and sys.version_info >= (3, 13):
                    kind = 'array' if key is None else 'object'
                    raise json.JSONDecodeError(
                        'Illegal trailing comma before end of ' + kind, text, comma)
                if key is not None:
                    key, pos = self.object_key(text, pos)
                    stack[-1] = (container, key)
                break
            else:
                return value, pos

    def decode(self, text: str) -> Any:
        try:
            value, end = self.scan(text, self.whitespace(text, 0).end())
        except StopIteration as exc:
            raise json.JSONDecodeError('Expecting value', text, exc.value) from None
        end = self.whitespace(text, end).end()
        if end != len(text):
            raise json.JSONDecodeError('Extra data', text, end)
        return value


class _SafeLoader(yaml.SafeLoader):
    def __init__(self, text: str, check: Callable[[], None]) -> None:
        self.check = check
        self._peeks = 0
        self._forwarded = 0
        super().__init__(text)

    def check_printable(self, data: str) -> None:
        for pos in range(0, len(data), _WINDOW):
            self.check()
            match = self.NON_PRINTABLE.search(data, pos, pos + _WINDOW)
            if match:
                raise yaml.reader.ReaderError(
                    self.name, self.index + len(self.buffer) - self.pointer + match.start(),
                    ord(match.group()), 'unicode', 'special characters are not allowed')
        self.check()

    def peek(self, index: int = 0) -> str:
        self._peeks += 1
        if self._peeks >= _WINDOW:
            self._peeks = 0
            self.check()
        return cast(str, super().peek(index))

    def prefix(self, length: int = 1) -> str:
        self.check()
        result = super().prefix(length)
        self.check()
        return cast(str, result)

    def forward(self, length: int = 1) -> None:
        while length:
            if self._forwarded >= _WINDOW:
                self._forwarded = 0
                self.check()
            batch = min(length, _WINDOW - self._forwarded)
            super().forward(batch)
            self._forwarded += batch
            length -= batch

    def compose_node(self, parent: Any, index: Any) -> Any:
        self.check()
        result = super().compose_node(parent, index)
        self.check()
        return result

    def construct_object(self, node: Any, deep: bool = False) -> Any:
        self.check()
        result = super().construct_object(node, deep=deep)
        self.check()
        return result

    def flatten_mapping(self, node: Any) -> None:
        # Retain SafeConstructor's in-place removal and reversed merge precedence,
        # but checkpoint the assembly loop as well as source-node traversal.
        merge: list[Any] = []
        index = 0
        while index < len(node.value):
            self.check()
            key_node, value_node = node.value[index]
            if key_node.tag == 'tag:yaml.org,2002:merge':
                del node.value[index]
                if isinstance(value_node, yaml.nodes.MappingNode):
                    self.flatten_mapping(value_node)
                    self._extend_merge(merge, value_node.value)
                elif isinstance(value_node, yaml.nodes.SequenceNode):
                    submerge = []
                    for subnode in value_node.value:
                        self.check()
                        if not isinstance(subnode, yaml.nodes.MappingNode):
                            raise yaml.constructor.ConstructorError(
                                'while constructing a mapping', node.start_mark,
                                'expected a mapping for merging, but found %s' % subnode.id,
                                subnode.start_mark)
                        self.flatten_mapping(subnode)
                        submerge.append(subnode.value)
                    for values in reversed(submerge):
                        self.check()
                        self._extend_merge(merge, values)
                else:
                    raise yaml.constructor.ConstructorError(
                        'while constructing a mapping', node.start_mark,
                        'expected a mapping or list of mappings for merging, but found %s'
                        % value_node.id, value_node.start_mark)
            else:
                if key_node.tag == 'tag:yaml.org,2002:value':
                    key_node.tag = 'tag:yaml.org,2002:str'
                index += 1
        if merge:
            self._extend_merge(merge, node.value)
            node.value = merge
        self.check()

    def _extend_merge(self, merge: list[Any], values: list[Any]) -> None:
        for pos in range(0, len(values), _WINDOW):
            self.check()
            merge.extend(values[pos:pos + _WINDOW])
        self.check()


def _yaml_decode(text: str, check: Callable[[], None] | None) -> Any:
    if check is None:
        return yaml.safe_load(text)
    loader = _SafeLoader.__new__(_SafeLoader)
    try:
        _SafeLoader.__init__(loader, text, check)
        return loader.get_single_data()
    finally:
        loader.dispose()


def read_import_document(path: Path, checkpoint: Callable[[], None] | None = None) -> Any:
    """Read JSON first except YAML suffixes, retaining original fallback errors.

    The caller protects checkpoint exceptions before entering parser translation.
    """
    text = path.read_text(encoding='utf-8') if checkpoint is None else _read_text(path, checkpoint)
    if path.suffix.lower() in ('.yaml', '.yml'):
        return _yaml_decode(text, checkpoint)
    try:
        return json.loads(text) if checkpoint is None else _JSONParser(checkpoint).decode(text)
    except json.JSONDecodeError as original:
        try:
            result = _yaml_decode(text, checkpoint)
            if not isinstance(result, (dict, list)):
                raise original
            return result
        except _CheckpointRaised:
            raise
        except Exception:
            raise original
