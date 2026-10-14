"""Tests for RequestData hidden_response_fields model, persistence, and RequestEditor UI."""

from __future__ import annotations

import json
import unittest

import pytest
from pydantic import ValidationError

from pypost.core.request_persisted_fields import (
    _PERSISTED_FIELD_NAMES,
    copy_request_for_isolated_tab,
    factory_request_draft,
    persisted_fields_equal,
    request_draft_fields_equal,
)
from pypost.models.models import Collection, RequestData
from pypost.ui import widget_ids
from pypost.ui.widgets.request_editor import RequestWidget

try:
    from pypost.ui.widgets.hidden_fields_table import HiddenFieldsTable
except ImportError:
    try:
        from pypost.ui.widgets.request_editor import HiddenFieldsTable  # type: ignore[assignment]
    except ImportError:
        HiddenFieldsTable = None  # type: ignore[assignment]

pytestmark = pytest.mark.timeout(30)


class TestRequestDataHiddenFieldsModel(unittest.TestCase):
    """Schema validation and default factory behavior for hidden_response_fields."""

    def test_request_data_schema_declares_hidden_response_fields(self):
        self.assertIn("hidden_response_fields", RequestData.model_fields)

    def test_request_data_default_hidden_fields(self):
        req = RequestData()
        self.assertTrue(
            hasattr(req, "hidden_response_fields"),
            "RequestData must have 'hidden_response_fields' attribute",
        )
        self.assertEqual(req.hidden_response_fields, [])
        self.assertIsInstance(req.hidden_response_fields, list)
        req2 = RequestData()
        self.assertIsNot(req.hidden_response_fields, req2.hidden_response_fields)

    def test_request_data_explicit_hidden_fields(self):
        req = RequestData(hidden_response_fields=["token", "secret", "user.password"])
        self.assertTrue(
            hasattr(req, "hidden_response_fields"),
            "RequestData must have 'hidden_response_fields' attribute",
        )
        self.assertEqual(
            req.hidden_response_fields,
            ["token", "secret", "user.password"],
        )

    def test_request_data_rejects_non_string_elements(self):
        with self.assertRaises(ValidationError):
            RequestData(hidden_response_fields=[{"invalid": "dict"}])
        with self.assertRaises(ValidationError):
            RequestData(hidden_response_fields="not-a-list")


class TestCollectionHiddenFieldsPersistence(unittest.TestCase):
    """Serialization round-trip and backward-compatible collection persistence."""

    def test_collection_serialization_round_trip(self):
        req = RequestData(name="Auth Req", hidden_response_fields=["token", "secret"])
        col = Collection(name="Secure API", requests=[req])
        payload_str = col.model_dump_json(indent=2)
        payload = json.loads(payload_str)
        self.assertIn(
            "hidden_response_fields",
            payload["requests"][0],
            "Serialized request JSON must contain 'hidden_response_fields'",
        )
        self.assertEqual(
            payload["requests"][0]["hidden_response_fields"],
            ["token", "secret"],
        )
        restored = Collection.model_validate_json(payload_str)
        self.assertTrue(hasattr(restored.requests[0], "hidden_response_fields"))
        self.assertEqual(
            restored.requests[0].hidden_response_fields,
            ["token", "secret"],
        )

    def test_legacy_collection_backward_compatibility(self):
        legacy_json = json.dumps(
            {
                "id": "col-legacy-1",
                "name": "Legacy Col",
                "requests": [
                    {
                        "id": "req-legacy-1",
                        "name": "Legacy Request",
                        "method": "GET",
                        "url": "https://api.example.com/data",
                    }
                ],
            }
        )
        loaded = Collection.model_validate_json(legacy_json)
        self.assertTrue(
            hasattr(loaded.requests[0], "hidden_response_fields"),
            "Loaded legacy request must have 'hidden_response_fields' attribute",
        )
        self.assertEqual(loaded.requests[0].hidden_response_fields, [])


class TestTabCopyIsolationHiddenFields(unittest.TestCase):
    """Tab copy isolation deep copying for hidden_response_fields."""

    def test_tab_copy_isolation_deep_copies_hidden_fields(self):
        original = RequestData(name="Source", hidden_response_fields=["token", "apiKey"])
        self.assertTrue(
            hasattr(original, "hidden_response_fields"),
            "RequestData must have 'hidden_response_fields' attribute",
        )
        isolated = copy_request_for_isolated_tab(original)
        self.assertTrue(
            hasattr(isolated, "hidden_response_fields"),
            "Isolated copy must have 'hidden_response_fields' attribute",
        )
        self.assertEqual(isolated.hidden_response_fields, ["token", "apiKey"])
        self.assertIsNot(
            isolated.hidden_response_fields,
            original.hidden_response_fields,
            "Isolated copy must own an independent list instance",
        )
        isolated.hidden_response_fields.append("session_id")
        self.assertEqual(
            original.hidden_response_fields,
            ["token", "apiKey"],
            "Mutating isolated copy must not alter original request",
        )
        self.assertEqual(
            isolated.hidden_response_fields,
            ["token", "apiKey", "session_id"],
        )


class TestPersistedFieldsDirtyTracking(unittest.TestCase):
    """Dirty tracking and draft equality for hidden_response_fields."""

    def test_persisted_field_names_registry_includes_hidden_response_fields(self):
        self.assertIn("hidden_response_fields", _PERSISTED_FIELD_NAMES)

    def test_persisted_fields_equal_detects_hidden_fields_diff(self):
        a = RequestData(name="Req", hidden_response_fields=["token"])
        b = RequestData(name="Req", hidden_response_fields=["token"])
        c = RequestData(name="Req", hidden_response_fields=["token", "extra"])
        self.assertTrue(
            hasattr(a, "hidden_response_fields"),
            "RequestData must have 'hidden_response_fields' attribute",
        )
        self.assertTrue(persisted_fields_equal(a, b))
        self.assertFalse(
            persisted_fields_equal(a, c),
            "persisted_fields_equal must return False when hidden_response_fields differ",
        )

    def test_request_draft_dirty_checking(self):
        draft = factory_request_draft()
        self.assertTrue(
            hasattr(draft, "hidden_response_fields"),
            "RequestData draft must have 'hidden_response_fields' attribute",
        )
        self.assertTrue(request_draft_fields_equal(draft, factory_request_draft()))
        draft.hidden_response_fields = ["auth.token"]
        self.assertFalse(
            request_draft_fields_equal(draft, factory_request_draft()),
            "request_draft_fields_equal must return False when draft hidden fields are modified",
        )


@pytest.mark.usefixtures("qapp")
class TestRequestEditorHiddenFieldsUI(unittest.TestCase):
    """RequestWidget 'Hidden Fields' detail tab and HiddenFieldsTable integration."""

    def setUp(self):
        self.widget = RequestWidget()

    def tearDown(self):
        self.widget.close()
        self.widget.deleteLater()

    def test_request_editor_has_hidden_fields_tab(self):
        tab_labels = [
            self.widget.detail_tabs.tabText(i)
            for i in range(self.widget.detail_tabs.count())
        ]
        self.assertIn("Hidden Fields", tab_labels)
        self.assertTrue(
            hasattr(self.widget, "hidden_fields_table"),
            "RequestWidget must expose 'hidden_fields_table' attribute",
        )
        expected_id = getattr(
            widget_ids,
            "REQUEST_HIDDEN_FIELDS_TABLE",
            "pypost_request_hidden_fields_table",
        )
        self.assertEqual(self.widget.hidden_fields_table.objectName(), expected_id)
        self.assertIsNotNone(
            HiddenFieldsTable,
            "HiddenFieldsTable class must be defined in pypost.ui.widgets.hidden_fields_table",
        )
        self.assertIsInstance(self.widget.hidden_fields_table, HiddenFieldsTable)

    def test_request_editor_loads_hidden_fields(self):
        req = RequestData(hidden_response_fields=["token", "apiKey"])
        self.assertTrue(
            hasattr(req, "hidden_response_fields"),
            "RequestData must have 'hidden_response_fields' attribute",
        )
        self.widget.request_data = req
        self.widget.load_data()
        self.assertTrue(
            hasattr(self.widget, "hidden_fields_table"),
            "RequestWidget must expose 'hidden_fields_table' attribute",
        )
        self.assertEqual(
            self.widget.hidden_fields_table.get_data(),
            ["token", "apiKey"],
        )

    def test_request_editor_get_request_data_extracts_table(self):
        self.assertTrue(
            hasattr(self.widget, "hidden_fields_table"),
            "RequestWidget must expose 'hidden_fields_table' attribute",
        )
        self.widget.hidden_fields_table.set_data(["auth.token", "secret_key"])
        draft = self.widget.get_request_data_from_ui()
        self.assertTrue(
            hasattr(draft, "hidden_response_fields"),
            "Extracted RequestData must have 'hidden_response_fields' attribute",
        )
        self.assertEqual(draft.hidden_response_fields, ["auth.token", "secret_key"])

        self.widget.update_request_data()
        self.assertTrue(
            hasattr(self.widget.request_data, "hidden_response_fields"),
            "Updated self.request_data must have 'hidden_response_fields' attribute",
        )
        self.assertEqual(
            self.widget.request_data.hidden_response_fields,
            ["auth.token", "secret_key"],
        )

    def test_request_editor_clearing_or_empty_reset(self):
        self.assertTrue(
            hasattr(self.widget, "hidden_fields_table"),
            "RequestWidget must expose 'hidden_fields_table' attribute",
        )
        self.widget.request_data = RequestData()
        self.widget.load_data()
        self.assertEqual(self.widget.hidden_fields_table.get_data(), [])
        self.assertEqual(self.widget.hidden_fields_table.rowCount(), 1)
        item = self.widget.hidden_fields_table.item(0, 0)
        self.assertTrue(item is None or item.text() == "")


if __name__ == "__main__":
    unittest.main()
