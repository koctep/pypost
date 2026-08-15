"""Tests for the shared JSON export root-shape policy (PYPOST-1010)."""

import pytest

from pypost.core.json_export_root import json_root_for_records

pytestmark = pytest.mark.timeout(30)


def test_one_record_uses_object_root_without_copying_record():
    record = {"name": "Billing"}

    result = json_root_for_records([record])

    assert result is record


def test_many_records_keep_list_root_and_order():
    records = [{"name": "Billing"}, {"name": "Reporting"}]

    result = json_root_for_records(records)

    assert result is records


def test_no_records_keep_empty_list_root():
    records: list[dict] = []

    result = json_root_for_records(records)

    assert result is records
