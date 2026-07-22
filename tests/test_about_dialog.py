"""Tests for AboutDialog."""

import pytest
from PySide6.QtWidgets import QLabel

from pypost.ui.dialogs.about_dialog import AboutDialog
from pypost.version import __version__

pytestmark = pytest.mark.timeout(60)

def test_about_dialog_shows_package_version(qapp):
    dlg = AboutDialog()
    try:
        labels = dlg.findChildren(QLabel)
        version_texts = [label.text() for label in labels if label.text().startswith("Version")]
        assert version_texts == [f"Version {__version__}"]
    finally:
        dlg.close()
