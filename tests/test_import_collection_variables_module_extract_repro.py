"""Failing repro for PYPOST-1423: virtualization components extracted from dialog.

Asserts that either the import dialog module is under 500 LOC, or the four
virtualization classes live in their dedicated target modules (and are not
defined inline in the dialog source). Before the extract both conditions fail.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(30)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DIALOG_PATH = (
    _REPO_ROOT / "pypost" / "ui" / "dialogs" / "import_collection_variables_dialog.py"
)

_TARGET_DEFINITIONS: dict[str, Path] = {
    "CollectionVariablesTableModel": (
        _REPO_ROOT / "pypost" / "ui" / "models" / "collection_variables_table_model.py"
    ),
    "ConflictStrategyDelegate": (
        _REPO_ROOT / "pypost" / "ui" / "delegates" / "conflict_strategy_delegate.py"
    ),
    "CollectionVariablesTableView": (
        _REPO_ROOT / "pypost" / "ui" / "views" / "collection_variables_table_view.py"
    ),
    "CollectionFetchWorker": (
        _REPO_ROOT / "pypost" / "ui" / "workers" / "collection_fetch_worker.py"
    ),
}


def _count_physical_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _class_names_defined_in(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in tree.body if isinstance(node, ast.ClassDef)}


def _classes_live_in_target_modules() -> bool:
    dialog_classes = _class_names_defined_in(_DIALOG_PATH)
    for class_name, target_path in _TARGET_DEFINITIONS.items():
        if class_name in dialog_classes:
            return False
        if class_name not in _class_names_defined_in(target_path):
            return False
    return True


@pytest.mark.timeout(30)
def test_import_collection_variables_virtualization_components_extracted() -> None:
    """Dialog LOC < 500 OR virtualization classes defined only in target modules."""
    assert _DIALOG_PATH.is_file(), f"Missing dialog module: {_DIALOG_PATH}"
    dialog_loc = _count_physical_lines(_DIALOG_PATH)
    extracted = _classes_live_in_target_modules()
    targets = {k: str(v) for k, v in _TARGET_DEFINITIONS.items()}
    assert dialog_loc < 500 or extracted, (
        f"Expected dialog LOC < 500 or classes in target modules; "
        f"got dialog_loc={dialog_loc}, extracted={extracted}. "
        f"Targets: {targets}"
    )
