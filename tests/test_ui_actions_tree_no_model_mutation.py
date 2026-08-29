"""PYPOST-1042 / PYPOST-972 TD-1: Evidence that test_select_tree_no_model_raises is load-bearing.

Proves that the contract test in ``tests/test_ui_actions.py`` genuinely guards the
tree-no-model refusal path by showing it fails when the production guard in
``_select_tree`` is deleted or reworded.
"""

from __future__ import annotations

import inspect
import textwrap
from typing import Callable

import pytest
from PySide6.QtWidgets import QApplication

import pypost.agent.ui_actions as ui_actions
import tests.test_ui_actions as ui_actions_suite

pytestmark = [pytest.mark.timeout(60), pytest.mark.agent_e2e]

_GUARD_ANCHOR = (
    '    model = widget.model()\n'
    '    if model is None:\n'
    '        raise UiTargetNotInteractableError(widget_id, "tree has no model")'
)

_REWORDED_GUARD = (
    '    model = widget.model()\n'
    '    if model is None:\n'
    '        raise UiTargetNotInteractableError(widget_id, "item view has no model")'
)


def _contract_test() -> Callable[..., None]:
    """Resolve the contract test from tests/test_ui_actions.py or fail with a clear message."""
    test_func = getattr(ui_actions_suite, "test_select_tree_no_model_raises", None)
    if test_func is None:
        raise AssertionError(
            "tests/test_ui_actions.py must define test_select_tree_no_model_raises "
            "(PYPOST-1042 contract test)"
        )
    return test_func


def _mutant_select_tree(mutate_source: Callable[[str], str]) -> Callable[..., None]:
    """Derive a mutant _select_tree from the real production source and compile it."""
    orig_src = textwrap.dedent(inspect.getsource(ui_actions._select_tree))
    mutated_src = mutate_source(orig_src)
    assert mutated_src != orig_src, "Mutator failed to change _select_tree source"

    scope = dict(ui_actions.__dict__)
    exec(compile(mutated_src, "<mutant _select_tree>", "exec"), scope)  # noqa: S102
    return scope["_select_tree"]


def _install_mutant(monkeypatch: pytest.MonkeyPatch, mutant: Callable[..., None]) -> None:
    """Monkeypatch _select_tree in pypost.agent.ui_actions in-memory for the test."""
    monkeypatch.setattr(ui_actions, "_select_tree", mutant)


def _remove_guard(source: str) -> str:
    """Delete the model is None guard check from _select_tree source."""
    assert _GUARD_ANCHOR in source, (
        f"Guard anchor not found in _select_tree source: {_GUARD_ANCHOR!r}"
    )
    # Replace the guard with just getting the model
    return source.replace(_GUARD_ANCHOR, "    model = widget.model()")


def _reword_guard(source: str) -> str:
    """Reword the tree has no model reason to item view has no model."""
    assert _GUARD_ANCHOR in source, (
        f"Guard anchor not found in _select_tree source: {_GUARD_ANCHOR!r}"
    )
    return source.replace(_GUARD_ANCHOR, _REWORDED_GUARD)


def test_repro_contract_catches_guard_removed_text_option(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Removing the guard causes selection by text to fail contract (reason differs)."""
    contract_fn = _contract_test()
    mutant = _mutant_select_tree(_remove_guard)
    _install_mutant(monkeypatch, mutant)

    with pytest.raises(AssertionError, match=r"tree has no model"):
        contract_fn(qapp, "Alpha")


def test_repro_contract_catches_guard_removed_index_option(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Removing the guard causes selection by index to crash on model.rowCount()."""
    contract_fn = _contract_test()
    mutant = _mutant_select_tree(_remove_guard)
    _install_mutant(monkeypatch, mutant)

    with pytest.raises(AttributeError, match=r"rowCount"):
        contract_fn(qapp, 0)


@pytest.mark.parametrize("option", ["Alpha", 0], ids=["by-text", "by-index"])
def test_repro_contract_catches_reason_reworded(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    option: str | int,
) -> None:
    """Rewording reason to 'item view has no model' fails both positive and negative asserts."""
    contract_fn = _contract_test()
    mutant = _mutant_select_tree(_reword_guard)
    _install_mutant(monkeypatch, mutant)

    with pytest.raises(AssertionError):
        contract_fn(qapp, option)
