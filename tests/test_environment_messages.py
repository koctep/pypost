"""Unit tests for centralized environment UI string constants."""

import pytest

from pypost.core.environment_messages import (
    MSG_COPY_OF_NAME,
    MSG_DELETE_ENVIRONMENT_CONFIRM,
    MSG_DUPLICATE_ENVIRONMENT_NAME,
    format_copy_of_name,
    format_delete_environment_confirm,
    format_duplicate_environment_name,
)

pytestmark = pytest.mark.timeout(10)


def test_format_copy_of_name():
    assert format_copy_of_name("Dev") == MSG_COPY_OF_NAME.format(name="Dev")


def test_format_delete_environment_confirm():
    assert format_delete_environment_confirm("Prod") == MSG_DELETE_ENVIRONMENT_CONFIRM.format(
        name="Prod",
    )


def test_format_duplicate_environment_name():
    assert format_duplicate_environment_name("Staging") == (
        MSG_DUPLICATE_ENVIRONMENT_NAME.format(name="Staging")
    )
