"""Shared JSON root-shape policy for exported record lists."""
from __future__ import annotations


def json_root_for_records(records: list[dict]) -> dict | list[dict]:
    """Return an object for one record and a list for every other count."""
    if len(records) == 1:
        return records[0]
    return records
