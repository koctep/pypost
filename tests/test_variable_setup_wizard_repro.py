"""Automated failing repro tests for PYPOST-1373: VariableSetupWizardDialog & VariableGuidanceCard.

Tests the missing UI components:
- VariableGuidanceCard (rendering, masking, collapsible guidance, inline validation)
- VariableSetupWizardDialog (rendering cards, scroll area, validation, accept/reject, extraction)
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QDialog, QLineEdit

from pypost.models.collection_variable import CollectionVariable

# Expected import target for Step 4
from pypost.ui.variable_setup_wizard_dialog import (
    VariableGuidanceCard,
    VariableSetupWizardDialog,
)

pytestmark = pytest.mark.timeout(30)


@pytest.mark.usefixtures("qapp")
def test_variable_guidance_card_rendering_and_defaults():
    """Card renders variable name, type label/badge, required indicator, and defaults."""
    var = CollectionVariable(
        name="API_KEY",
        type="string",
        default="default-key-123",
        description="Authentication key",
        help_text="Provide your API key from the provider dashboard.",
        required=True,
        secret=False,
    )
    card = VariableGuidanceCard(var)
    try:
        assert card.variable.name == "API_KEY"
        assert card.get_value() == "default-key-123"
        assert card.is_valid() is True

        # Initial value override takes precedence over default
        card_override = VariableGuidanceCard(var, initial_value="custom-key-456")
        try:
            assert card_override.get_value() == "custom-key-456"
        finally:
            card_override.close()
    finally:
        card.close()


@pytest.mark.usefixtures("qapp")
def test_variable_guidance_card_secret_masking_and_toggle():
    """Card masks secret variables with Password EchoMode and toggles with eye button."""
    secret_var = CollectionVariable(
        name="DB_PASSWORD",
        type="string",
        default="secret_pass",
        required=True,
        secret=True,
    )
    card = VariableGuidanceCard(secret_var)
    try:
        # Secret should default to Password echo mode
        input_widget = getattr(card, "input_field", None) or getattr(card, "_input_field", None)
        assert input_widget is not None, "VariableGuidanceCard must expose input widget"
        assert isinstance(input_widget, QLineEdit)
        assert input_widget.echoMode() == QLineEdit.EchoMode.Password

        # Toggling secret visibility switches to Normal
        assert hasattr(card, "toggle_secret_visibility")
        card.toggle_secret_visibility()
        assert input_widget.echoMode() == QLineEdit.EchoMode.Normal

        # Toggling again switches back to Password
        card.toggle_secret_visibility()
        assert input_widget.echoMode() == QLineEdit.EchoMode.Password
    finally:
        card.close()


@pytest.mark.usefixtures("qapp")
def test_variable_guidance_card_collapsible_guidance():
    """Card expands/collapses help text when present, and disables/omits toggle when absent."""
    # With guidance
    var_with_help = CollectionVariable(
        name="TENANT_ID",
        type="string",
        help_text="Find tenant ID under **Admin > Organization Settings**.",
        required=False,
    )
    card_with_help = VariableGuidanceCard(var_with_help)
    try:
        guidance_panel = getattr(card_with_help, "guidance_container", None) or getattr(
            card_with_help, "_guidance_container", None
        )
        assert guidance_panel is not None, "Guidance container must exist when help_text is present"
        # Initially collapsed / hidden
        assert guidance_panel.isVisible() is False

        # Toggle to expand
        card_with_help.toggle_guidance()
        assert guidance_panel.isVisible() is True

        # Toggle to collapse
        card_with_help.toggle_guidance()
        assert guidance_panel.isVisible() is False
    finally:
        card_with_help.close()

    # Without guidance (help_text is None)
    var_no_help = CollectionVariable(
        name="TIMEOUT_SEC",
        type="integer",
        default=30,
        help_text=None,
        required=False,
    )
    card_no_help = VariableGuidanceCard(var_no_help)
    try:
        toggle_btn = getattr(card_no_help, "guidance_toggle_button", None) or getattr(
            card_no_help, "_guidance_toggle_btn", None
        )
        # Toggle button should either be None, hidden, or disabled
        if toggle_btn is not None:
            assert toggle_btn.isVisible() is False or not toggle_btn.isEnabled()
    finally:
        card_no_help.close()


@pytest.mark.usefixtures("qapp")
def test_variable_guidance_card_inline_validation():
    """Card validation: empty required variable fails is_valid(); typing clears error."""
    required_var = CollectionVariable(
        name="MANDATORY_URL",
        type="string",
        required=True,
    )
    card = VariableGuidanceCard(required_var)
    try:
        assert card.is_valid() is False
        card.set_validation_error("This variable is required")

        error_label = getattr(card, "error_label", None) or getattr(card, "_error_label", None)
        assert error_label is not None
        assert "required" in error_label.text().lower()

        # Typing value clears error and becomes valid
        card.set_value("https://api.example.com")
        assert card.is_valid() is True
    finally:
        card.close()


@pytest.mark.usefixtures("qapp")
def test_variable_setup_wizard_dialog_flow_and_extraction():
    """Wizard dialog displays cards in scroll area, validates on accept, and extracts values."""
    variables = [
        CollectionVariable(name="BASE_URL", type="string", required=True),
        CollectionVariable(name="API_SECRET", type="string", required=True, secret=True),
        CollectionVariable(name="MAX_RETRIES", type="integer", default=3, required=False),
    ]
    initial_values = {"BASE_URL": "https://pypost.dev"}

    dialog = VariableSetupWizardDialog(variables=variables, initial_values=initial_values)
    try:
        # Should contain cards for all variables
        cards = getattr(dialog, "cards", None) or getattr(dialog, "_cards", None)
        assert cards is not None
        assert len(cards) == 3

        # BASE_URL has initial value, but API_SECRET is empty and required -> invalid
        assert dialog.validate_all() is False

        # Attempting accept() while invalid must block dialog acceptance
        dialog.accept()
        assert dialog.result() != QDialog.DialogCode.Accepted

        # Provide missing required value
        if "API_SECRET" in cards:
            cards["API_SECRET"].set_value("super_secret_token")
        else:
            # If cards is a list, find matching card
            for c in cards:
                if c.variable.name == "API_SECRET":
                    c.set_value("super_secret_token")
                    break

        assert dialog.validate_all() is True

        # Now accept() should succeed
        dialog.accept()
        assert dialog.result() == QDialog.DialogCode.Accepted

        # Extract values
        values = dialog.get_values()
        assert values["BASE_URL"] == "https://pypost.dev"
        assert values["API_SECRET"] == "super_secret_token"
        assert values["MAX_RETRIES"] == 3 or values["MAX_RETRIES"] == "3"

        # Partitioned configuration
        configured = dialog.get_configured_variables()
        assert "overrides" in configured
        assert "secrets" in configured
        assert configured["overrides"]["BASE_URL"] == "https://pypost.dev"
        assert configured["secrets"]["API_SECRET"] == "super_secret_token"
    finally:
        dialog.close()
