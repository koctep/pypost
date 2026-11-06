"""JSON escaping helpers for request-body templates (PYPOST-1283, PYPOST-1343).

Several bundled request-body templates interpolate free-form values (an
issue summary, a project key, an issue-type name) directly into a JSON
string literal inside a Jinja template, e.g.::

    "summary": "{{ summary_value }}"

Because ``{{ }}`` substitution is a raw string paste, any double quote or
backslash in the interpolated value produces invalid JSON and can even let
an attacker break out of the string literal and inject additional JSON
fields. ``to_adf`` already avoids this for the description field by
internally calling ``json.dumps``; ``to_json_string`` provides the same
safety for any other plain string field.

``to_json`` (PYPOST-1343) serializes lists, dicts, booleans, numbers, and
strings with their native JSON types so authors do not hand-build arrays
or objects with Jinja loops. Use ``to_json_string`` when the slot must be
a JSON string; use ``to_json`` when the value's JSON type must be
preserved.

Both functions are registered as Jinja globals in
``pypost.core.function_registry``.
"""
from __future__ import annotations

import json


def to_json_string(text: object) -> str:
    """Return a JSON-serialized string literal for ``text``.

    Unlike bare ``{{ value }}`` interpolation, this escapes double quotes,
    backslashes, control characters, and any other character JSON string
    literals require escaped, and wraps the result in the surrounding
    quotes. It is meant to be substituted unquoted into a JSON template,
    e.g. ``"summary": {{ to_json_string(summary_value) }}``.

    Args:
        text: Value to serialize. Non-string values are coerced with
            ``str()`` first so the function is safe to call on template
            values that may already be plain text.

    Returns:
        A JSON string literal (including the surrounding double quotes),
        suitable for direct substitution into a JSON request body
        template.
    """
    if text is None:
        text = ""
    return json.dumps(str(text))


def to_json(value: object) -> str:
    """Return JSON text for ``value`` with native JSON types preserved.

    Unlike ``to_json_string``, this does not coerce the value to ``str``
    first. Lists become JSON arrays, dicts become objects, booleans and
    numbers keep their JSON types, and ``None`` becomes ``null``. The
    result is meant to be substituted unquoted into a JSON template,
    e.g. ``"labels": {{ to_json(mcp.request.labels) }}``.

    Args:
        value: Value to serialize. Must be JSON-serializable.

    Returns:
        A JSON fragment (array, object, string, number, boolean, or null)
        suitable for direct substitution into a JSON request body
        template.

    Raises:
        TypeError: If ``value`` is not JSON-serializable.
    """
    return json.dumps(value, ensure_ascii=False)
