"""Tests for pypost.core.environment_messages."""

import pytest

pytestmark = pytest.mark.timeout(60)

from pypost.core.environment_messages import (
    MSG_COPY_OF_NAME,
    MSG_DELETE_ENVIRONMENT_CONFIRM,
    MSG_DUPLICATE_ENVIRONMENT_NAME,
    MSG_EMPTY_NAME,
    format_copy_of_name,
    format_delete_environment_confirm,
    format_duplicate_environment_name,
)


class TestEnvironmentMessageFormatters:
    def test_format_delete_environment_confirm(self) -> None:
        assert format_delete_environment_confirm("Prod") == MSG_DELETE_ENVIRONMENT_CONFIRM.format(
            name="Prod",
        )

    def test_format_duplicate_environment_name(self) -> None:
        assert format_duplicate_environment_name("Staging") == (
            MSG_DUPLICATE_ENVIRONMENT_NAME.format(name="Staging")
        )

    def test_format_copy_of_name(self) -> None:
        assert format_copy_of_name("Dev") == MSG_COPY_OF_NAME.format(name="Dev")

    def test_empty_name_constant(self) -> None:
        assert MSG_EMPTY_NAME == "Name cannot be empty."
