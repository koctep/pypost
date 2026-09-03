"""Red repro for PYPOST-1184: shared insert-before-plus helper does not exist yet.

Step 2 architecture (ai-tasks/PYPOST-1184/20-architecture.md) calls for extracting the
"insert tab before the plus button / append + ensure plus tab / focus / conditional
save_tabs_state" sequence -- currently triplicated verbatim in ``add_new_tab``,
``_insert_mcp_client_tab``, and ``_insert_websocket_tab`` in
``pypost/ui/presenters/tabs_presenter.py`` -- into a single free function
``insert_tab_before_plus(presenter, tab, name, *, save_state=True)`` living in a new
sibling module ``pypost/ui/presenters/tabs_presenter_insert.py``.

This test is intentionally RED against current (pre-Step-4) code: the module does not
exist yet, so the import fails. It will turn green once Step 4 adds the module and the
three call sites are refactored to call through it (verified below via source
inspection, mirroring how the codebase already established the "presenter as first
positional arg" sibling-module extraction pattern for the *_close.py family).
"""

from __future__ import annotations

import inspect

import pytest

pytestmark = pytest.mark.timeout(30)


def test_insert_tab_before_plus_helper_module_exists():
    """The shared helper module/function from the architecture doc must exist."""
    # This import is expected to fail on current code (module does not exist yet).
    from pypost.ui.presenters.tabs_presenter_insert import insert_tab_before_plus

    sig = inspect.signature(insert_tab_before_plus)
    params = list(sig.parameters.values())

    # presenter, tab, name positional; save_state keyword-only with default True.
    assert [p.name for p in params[:3]] == ["presenter", "tab", "name"]
    assert params[0].kind in (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    )
    save_state_param = sig.parameters["save_state"]
    assert save_state_param.kind == inspect.Parameter.KEYWORD_ONLY
    assert save_state_param.default is True


def test_add_new_tab_delegates_to_shared_insert_helper():
    """`add_new_tab` must call through the shared helper, not hand-roll the sequence."""
    from pypost.ui.presenters import tabs_presenter

    source = inspect.getsource(tabs_presenter.TabsPresenter.add_new_tab)
    assert "insert_tab_before_plus(" in source
    assert "insert_index_before_plus()" not in source


def test_insert_mcp_client_tab_delegates_to_shared_insert_helper():
    """`_insert_mcp_client_tab` must call through the shared helper."""
    from pypost.ui.presenters import tabs_presenter

    source = inspect.getsource(tabs_presenter.TabsPresenter._insert_mcp_client_tab)
    assert "insert_tab_before_plus(" in source
    assert "insert_index_before_plus()" not in source


def test_insert_websocket_tab_delegates_to_shared_insert_helper():
    """`_insert_websocket_tab` must call through the shared helper."""
    from pypost.ui.presenters import tabs_presenter

    source = inspect.getsource(tabs_presenter.TabsPresenter._insert_websocket_tab)
    assert "insert_tab_before_plus(" in source
    assert "insert_index_before_plus()" not in source
