"""GUI tests for SaveRequestDialog (PYPOST-721)."""
import pytest

from unittest.mock import patch

from pypost.models.models import Collection
from pypost.ui.dialogs.save_dialog import SaveRequestDialog

pytestmark = pytest.mark.timeout(60)


class TestSaveRequestDialog:
    def test_construction_with_no_collections(self, qapp):
        dlg = SaveRequestDialog([])
        try:
            assert dlg.collection_combo.count() == 1  # only "Create New"
            assert not dlg.new_col_input.isHidden()  # index 0 → shown
        finally:
            dlg.close()

    def test_construction_populates_combo_with_collections(self, qapp):
        cols = [
            Collection(id="c1", name="API"),
            Collection(id="c2", name="Auth"),
        ]
        dlg = SaveRequestDialog(cols)
        try:
            assert dlg.collection_combo.count() == 3  # "Create New" + 2
            assert dlg.collection_combo.itemText(1) == "API"
            assert dlg.collection_combo.itemText(2) == "Auth"
        finally:
            dlg.close()

    def test_on_collection_changed_shows_new_col_input_at_index_0(self, qapp):
        cols = [Collection(id="c1", name="API")]
        dlg = SaveRequestDialog(cols)
        try:
            dlg.collection_combo.setCurrentIndex(1)
            assert dlg.new_col_input.isHidden()
            dlg.collection_combo.setCurrentIndex(0)
            assert not dlg.new_col_input.isHidden()
        finally:
            dlg.close()

    def test_validate_and_accept_empty_name_shows_warning(self, qapp):
        dlg = SaveRequestDialog([])
        try:
            dlg.name_input.setText("")
            with patch(
                "pypost.ui.dialogs.save_dialog.show_save_request_name_required"
            ) as mock_warn:
                dlg.validate_and_accept()
                mock_warn.assert_called_once()
            assert not dlg.isVisible() or not dlg.result()
        finally:
            dlg.close()

    def test_validate_and_accept_empty_collection_name_shows_warning(self, qapp):
        dlg = SaveRequestDialog([])
        try:
            dlg.name_input.setText("My Request")
            dlg.collection_combo.setCurrentIndex(0)
            dlg.new_col_input.setText("")
            with patch(
                "pypost.ui.dialogs.save_dialog.show_save_collection_name_required"
            ) as mock_warn:
                dlg.validate_and_accept()
                mock_warn.assert_called_once()
        finally:
            dlg.close()

    def test_validate_and_accept_creates_new_collection(self, qapp):
        dlg = SaveRequestDialog([])
        try:
            dlg.name_input.setText("My Request")
            dlg.collection_combo.setCurrentIndex(0)
            dlg.new_col_input.setText("New Coll")
            dlg.validate_and_accept()
            assert dlg.request_name == "My Request"
            assert dlg.new_collection_name == "New Coll"
            assert dlg.selected_collection_id is None
        finally:
            dlg.close()

    def test_validate_and_accept_selects_existing_collection(self, qapp):
        cols = [Collection(id="c1", name="API")]
        dlg = SaveRequestDialog(cols)
        try:
            dlg.name_input.setText("My Request")
            dlg.collection_combo.setCurrentIndex(1)
            dlg.validate_and_accept()
            assert dlg.request_name == "My Request"
            assert dlg.selected_collection_id == "c1"
            assert dlg.new_collection_name is None
        finally:
            dlg.close()
