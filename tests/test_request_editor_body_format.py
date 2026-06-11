import pytest

pytestmark = pytest.mark.timeout(60)

import sys
import unittest
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from pypost.models.models import RequestData
from pypost.ui.widgets.fold import BodyFormat
from pypost.ui.widgets.request_editor import (
    RequestWidget,
    body_format_to_body_type,
    body_type_to_body_format,
)

_app = None


def _get_app():
    global _app
    if _app is None:
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


class TestBodyFormatMapping(unittest.TestCase):
    def test_body_type_to_format_json(self):
        self.assertEqual(body_type_to_body_format("json"), BodyFormat.JSON)

    def test_body_type_to_format_yaml(self):
        self.assertEqual(body_type_to_body_format("yaml"), BodyFormat.YAML)

    def test_body_type_to_format_xml(self):
        self.assertEqual(body_type_to_body_format("xml"), BodyFormat.XML)

    def test_body_type_unknown_defaults_json(self):
        self.assertEqual(body_type_to_body_format("text"), BodyFormat.JSON)

    def test_body_format_to_body_type(self):
        self.assertEqual(body_format_to_body_type(BodyFormat.YAML), "yaml")


class TestRequestWidgetBodyFormat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _get_app()

    def setUp(self):
        self.widget = RequestWidget()

    def tearDown(self):
        self.widget.close()
        self.widget.deleteLater()

    def test_default_format_is_json(self):
        self.assertEqual(self.widget.body_format_combo.currentData(), BodyFormat.JSON)

    def test_load_data_restores_yaml_format(self):
        self.widget.request_data = RequestData(body_type="yaml")
        self.widget.load_data()
        self.assertEqual(self.widget.body_format_combo.currentData(), BodyFormat.YAML)

    def test_format_change_calls_set_body_format(self):
        self.widget.body_edit.set_body_format = MagicMock()
        self.widget.body_edit.set_body_format.reset_mock()
        index = self.widget.body_format_combo.findData(BodyFormat.XML)
        self.widget.body_format_combo.setCurrentIndex(index)
        self.widget.body_edit.set_body_format.assert_called_with(BodyFormat.XML)

    def test_get_request_data_persists_body_type(self):
        index = self.widget.body_format_combo.findData(BodyFormat.YAML)
        self.widget.body_format_combo.setCurrentIndex(index)
        data = self.widget.get_request_data_from_ui()
        self.assertEqual(data.body_type, "yaml")

    def test_load_data_sets_editor_format(self):
        self.widget.body_edit.set_body_format = MagicMock()
        self.widget.request_data = RequestData(body_type="xml")
        self.widget.load_data()
        self.widget.body_edit.set_body_format.assert_called_with(BodyFormat.XML)

    def test_yaml_as_json_checkbox_enabled_only_for_yaml(self):
        self.assertFalse(self.widget.yaml_as_json_check.isEnabled())
        index = self.widget.body_format_combo.findData(BodyFormat.YAML)
        self.widget.body_format_combo.setCurrentIndex(index)
        self.assertTrue(self.widget.yaml_as_json_check.isEnabled())
        index = self.widget.body_format_combo.findData(BodyFormat.JSON)
        self.widget.body_format_combo.setCurrentIndex(index)
        self.assertFalse(self.widget.yaml_as_json_check.isEnabled())

    def test_load_data_restores_yaml_as_json_checked(self):
        self.widget.request_data = RequestData(body_type="yaml", yaml_as_json=True)
        self.widget.load_data()
        self.assertTrue(self.widget.yaml_as_json_check.isChecked())
        self.assertTrue(self.widget.yaml_as_json_check.isEnabled())

    def test_get_request_data_persists_yaml_as_json(self):
        index = self.widget.body_format_combo.findData(BodyFormat.YAML)
        self.widget.body_format_combo.setCurrentIndex(index)
        self.widget.yaml_as_json_check.setChecked(True)
        data = self.widget.get_request_data_from_ui()
        self.assertTrue(data.yaml_as_json)

    def test_yaml_as_json_persisted_when_format_not_yaml(self):
        self.widget.request_data = RequestData(body_type="yaml", yaml_as_json=True)
        self.widget.load_data()
        index = self.widget.body_format_combo.findData(BodyFormat.JSON)
        self.widget.body_format_combo.setCurrentIndex(index)
        self.assertFalse(self.widget.yaml_as_json_check.isEnabled())
        data = self.widget.get_request_data_from_ui()
        self.assertTrue(data.yaml_as_json)

    def test_yaml_as_json_synced_to_body_editor(self):
        self.widget.body_edit.set_yaml_as_json = MagicMock()
        index = self.widget.body_format_combo.findData(BodyFormat.YAML)
        self.widget.body_format_combo.setCurrentIndex(index)
        self.widget.yaml_as_json_check.setChecked(True)
        self.widget.body_edit.set_yaml_as_json.assert_called_with(True)
        self.widget.yaml_as_json_check.setChecked(False)
        self.widget.body_edit.set_yaml_as_json.assert_called_with(False)


if __name__ == "__main__":
    unittest.main()
