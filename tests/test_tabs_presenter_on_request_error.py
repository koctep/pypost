"""Pytest coverage for TabsPresenter._on_request_error (PYPOST-615)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pypost.models.settings import AppSettings
from pypost.ui.presenters.tabs_presenter import TabsPresenter
from tests.test_tabs_presenter import (
    FakeRequestManager,
    FakeStateManager,
    _make_request,
)


@pytest.fixture
def presenter_with_tab(qapp):
    rm = FakeRequestManager()
    sm = FakeStateManager()
    presenter = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())
    req = _make_request("r1", "Test", "GET")
    presenter.add_new_tab(req)
    tab = presenter.widget.widget(0)
    return presenter, tab


@pytest.mark.timeout(60)
def test_str_cancellation_message_no_dialog(presenter_with_tab) -> None:
    presenter, tab = presenter_with_tab
    with patch(
        "pypost.ui.presenters.tabs_presenter.show_request_failed_error"
    ) as mock_show:
        presenter._on_request_error(tab, "request cancelled")
        mock_show.assert_not_called()


@pytest.mark.timeout(60)
def test_str_error_shows_dialog(presenter_with_tab) -> None:
    presenter, tab = presenter_with_tab
    with patch(
        "pypost.ui.presenters.tabs_presenter.show_request_failed_error"
    ) as mock_show:
        presenter._on_request_error(tab, "connection refused")
        mock_show.assert_called_once()


@pytest.mark.timeout(60)
def test_execution_error_network_shows_category_message(presenter_with_tab) -> None:
    from pypost.models.errors import ErrorCategory, ExecutionError

    presenter, tab = presenter_with_tab
    exc = ExecutionError(
        category=ErrorCategory.NETWORK,
        message="no conn",
        detail="connection refused",
    )
    with patch("pypost.ui.presenters.tabs_presenter.show_request_error") as mock_show:
        presenter._on_request_error(tab, exc)
        mock_show.assert_called_once()
        assert "server is running" in mock_show.call_args[0][1]


@pytest.mark.timeout(60)
def test_execution_error_body_shows_category_message(presenter_with_tab) -> None:
    from pypost.models.errors import ErrorCategory, ExecutionError

    presenter, tab = presenter_with_tab
    exc = ExecutionError(
        category=ErrorCategory.BODY,
        message="Could not convert YAML body to JSON.",
        detail="mapping values are not allowed here",
    )
    with patch("pypost.ui.presenters.tabs_presenter.show_request_error") as mock_show:
        presenter._on_request_error(tab, exc)
        mock_show.assert_called_once()
        args = mock_show.call_args[0]
        assert "Could not convert YAML body to JSON" in args[1]
        assert "mapping values are not allowed here" in args[1]


@pytest.mark.timeout(60)
def test_execution_error_timeout_shows_timeout_message(presenter_with_tab) -> None:
    from pypost.models.errors import ErrorCategory, ExecutionError

    presenter, tab = presenter_with_tab
    exc = ExecutionError(
        category=ErrorCategory.TIMEOUT,
        message="timed out",
        detail="ReadTimeout",
    )
    with patch("pypost.ui.presenters.tabs_presenter.show_request_error") as mock_show:
        presenter._on_request_error(tab, exc)
        assert "timed out" in mock_show.call_args[0][1]


@pytest.mark.timeout(60)
def test_execution_error_detail_substring_not_treated_as_cancelled(
    presenter_with_tab,
) -> None:
    from pypost.models.errors import ErrorCategory, ExecutionError

    presenter, tab = presenter_with_tab
    exc = ExecutionError(
        category=ErrorCategory.NETWORK,
        message="connection failed",
        detail="operation cancelled by upstream proxy",
    )
    with patch("pypost.ui.presenters.tabs_presenter.show_request_error") as mock_show:
        presenter._on_request_error(tab, exc)
        mock_show.assert_called_once()


@pytest.mark.timeout(60)
def test_execution_error_cancelled_no_dialog(presenter_with_tab) -> None:
    from pypost.models.errors import ErrorCategory, ExecutionError

    presenter, tab = presenter_with_tab
    exc = ExecutionError(
        category=ErrorCategory.CANCELLED,
        message="Request cancelled",
        detail="Cancelled during retry delay",
    )
    with patch("pypost.ui.presenters.tabs_presenter.show_request_error") as mock_show:
        presenter._on_request_error(tab, exc)
        mock_show.assert_not_called()


@pytest.mark.timeout(60)
def test_execution_error_message_does_not_expose_raw_detail_for_network(
    presenter_with_tab,
) -> None:
    from pypost.models.errors import ErrorCategory, ExecutionError

    presenter, tab = presenter_with_tab
    raw_detail = "HTTPSConnectionPool(host='secret', port=443): Max retries exceeded"
    exc = ExecutionError(
        category=ErrorCategory.NETWORK,
        message="no conn",
        detail=raw_detail,
    )
    with patch("pypost.ui.presenters.tabs_presenter.show_request_error") as mock_show:
        presenter._on_request_error(tab, exc)
        assert raw_detail not in mock_show.call_args[0][1]
