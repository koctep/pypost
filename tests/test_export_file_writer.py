"""Tests for pypost.core.export_file_writer (PYPOST-1011)."""

import json
from pathlib import Path

import pytest

from pypost.core.export_file_writer import write_json_export_file

pytestmark = pytest.mark.timeout(60)


class _CustomError(Exception):
    """Local stand-in error class to verify the caller-supplied error_cls is used."""


def test_write_json_export_file_creates_parent_dirs_and_writes_indented_json(tmp_path):
    export_path = tmp_path / "nested" / "dir" / "export.json"

    write_json_export_file(
        export_path, {"name": "Dev", "variables": {}}, error_cls=_CustomError
    )

    assert export_path.parent.is_dir()
    text = export_path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert text == json.dumps({"name": "Dev", "variables": {}}, indent=2) + "\n"
    assert json.loads(text) == {"name": "Dev", "variables": {}}


def test_write_json_export_file_wraps_os_error_in_error_cls(tmp_path, monkeypatch):
    export_path = tmp_path / "export.json"

    def boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", boom)

    with pytest.raises(_CustomError, match="Could not write file"):
        write_json_export_file(export_path, {"name": "Dev"}, error_cls=_CustomError)


def test_write_json_export_file_wraps_non_serializable_payload_in_error_cls(tmp_path):
    export_path = tmp_path / "export.json"

    with pytest.raises(_CustomError, match="Could not write file"):
        write_json_export_file(
            export_path, {"name": "Dev", "bad": object()}, error_cls=_CustomError
        )


def test_write_json_export_file_uses_provided_error_cls_not_a_fixed_type(tmp_path):
    export_path = tmp_path / "export.json"

    class AnotherError(Exception):
        pass

    with pytest.raises(AnotherError, match="Could not write file"):
        write_json_export_file(
            export_path, {"bad": object()}, error_cls=AnotherError
        )
