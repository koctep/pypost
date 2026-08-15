"""Shared low-level JSON export write helper (PYPOST-1011).

No Qt dependency, no knowledge of any specific export domain: this module
owns the single real implementation of "write a JSON export payload to a
path," used by both ``pypost.core.collection_export`` and
``pypost.core.environment_export`` without either domain module importing
the other.
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["write_json_export_file"]


def write_json_export_file(
    path: Path,
    payload: object,
    *,
    error_cls: type[Exception],
) -> None:
    """Write ``payload`` to ``path`` as indented UTF-8 JSON with a trailing newline.

    Creates ``path``'s parent directories as needed. Wraps any failure to
    serialize or write (``OSError``, ``TypeError``, ``ValueError``) in
    ``error_cls(f"Could not write file: {exc}")``.

    Args:
        path: Destination file path.
        payload: JSON-serializable object to write.
        error_cls: Exception class to raise on failure.

    Raises:
        Exception: An instance of ``error_cls`` when the payload cannot be
            serialized or the file cannot be written.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, indent=2)
        path.write_text(text + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError) as exc:
        raise error_cls(f"Could not write file: {exc}") from exc
