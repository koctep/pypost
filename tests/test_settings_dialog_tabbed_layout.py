"""PYPOST-1145: SettingsDialog categorized tabbed layout contract tests."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QTabWidget, QWidget

from pypost.models.settings import AppSettings
from pypost.ui.dialogs.settings_dialog import (
    SETTINGS_TAB_LABELS,
    SettingsDialog,
)
from pypost.ui.widget_ids import SETTINGS_TABS

pytestmark = pytest.mark.timeout(60)


class TestSettingsDialogTabbedLayout:
    def test_settings_dialog_exposes_categorized_tabs(self, qapp):
        """Settings must use QTabWidget with documented category labels."""
        dlg = SettingsDialog(AppSettings())
        try:
            tabs = dlg.settings_tabs
            assert isinstance(tabs, QTabWidget)
            assert tabs.objectName() == SETTINGS_TABS
            labels = [tabs.tabText(index) for index in range(tabs.count())]
            assert labels == list(SETTINGS_TAB_LABELS)
        finally:
            dlg.close()

    def test_editor_controls_on_general_tab(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            general_page = dlg.settings_tabs.widget(0)
            assert isinstance(general_page, QWidget)
            assert dlg.form_layout_index_of(dlg.theme_combo) >= 0
            assert dlg.tab_form_layout(general_page).indexOf(dlg.theme_combo) >= 0
            assert dlg.tab_form_layout(general_page).indexOf(dlg.timeout_spin) < 0
        finally:
            dlg.close()

    def test_request_controls_on_requests_tab(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            requests_page = dlg.settings_tabs.widget(1)
            form = dlg.tab_form_layout(requests_page)
            assert form.indexOf(dlg.timeout_spin) >= 0
            assert form.indexOf(dlg.retryable_codes_edit) >= 0
            assert form.indexOf(dlg.theme_combo) < 0
        finally:
            dlg.close()

    def test_network_controls_on_network_tab(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            network_page = dlg.settings_tabs.widget(2)
            form = dlg.tab_form_layout(network_page)
            assert form.indexOf(dlg.mcp_host_edit) >= 0
            assert form.indexOf(dlg._websocket_section.max_concurrent_spin) >= 0
        finally:
            dlg.close()

    def test_security_controls_on_security_tab(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            security_page = dlg.settings_tabs.widget(3)
            form = dlg.tab_form_layout(security_page)
            assert form.indexOf(dlg.security_logging_section_label) >= 0
            assert form.indexOf(dlg.alert_log_path_edit) >= 0
            assert form.indexOf(dlg.retryable_codes_edit) < 0
        finally:
            dlg.close()

    def test_encryption_controls_on_encryption_tab(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            encryption_page = dlg.settings_tabs.widget(4)
            form = dlg.tab_form_layout(encryption_page)
            assert form.indexOf(dlg.env_encryption_mode_combo) >= 0
            assert form.indexOf(dlg.verify_encryption_btn) >= 0
        finally:
            dlg.close()
