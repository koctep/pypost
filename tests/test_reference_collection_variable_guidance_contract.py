"""Contract test suite for reference collection variable guidance (PYPOST-1375).

Validates that:
1. examples/collections/google_drive.json defines rich, actionable help_text on
   OAuth variables (Google Cloud Console, OAuth consent screen, credentials, scopes).
2. CollectionVariable models preserve and validate help_text fidelity upon loading.
3. VariableGuidanceCard and VariableSetupWizardDialog properly initialize guidance
   containers, toggle buttons, and secret masking for reference collection variables.
4. Backward compatibility is maintained for collections without guidance text.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtWidgets import QLineEdit

from pypost.core.collection_serializer import read_collection_file
from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection
from pypost.ui.variable_setup_wizard_dialog import (
    VariableGuidanceCard,
    VariableSetupWizardDialog,
)

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
GOOGLE_DRIVE_COLLECTION_PATH = REPO_ROOT / "examples" / "collections" / "google_drive.json"


@pytest.mark.timeout(30)
def test_google_drive_collection_has_rich_help_text() -> None:
    """Fixture examples/collections/google_drive.json must define rich help_text."""
    assert GOOGLE_DRIVE_COLLECTION_PATH.is_file(), (
        f"Expected collection file at {GOOGLE_DRIVE_COLLECTION_PATH}"
    )
    with open(GOOGLE_DRIVE_COLLECTION_PATH, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    variables: list[dict[str, Any]] = data.get("variables", [])
    token_var = next(
        (v for v in variables if v.get("name") == "google_drive_access_token"),
        None,
    )
    assert token_var is not None, "google_drive_access_token variable definition missing"
    assert "help_text" in token_var, "google_drive_access_token missing help_text key"
    help_text = token_var.get("help_text")
    assert isinstance(help_text, str) and help_text.strip(), (
        "google_drive_access_token help_text must be a non-empty string"
    )

    # Validate essential guidance components for OAuth setup
    assert "Google Cloud Console" in help_text
    assert "OAuth consent" in help_text
    assert "Credentials" in help_text
    assert "https://www.googleapis.com/auth/drive" in help_text


@pytest.mark.timeout(30)
def test_collection_variable_deserialization_fidelity() -> None:
    """Loading google_drive.json into CollectionVariable retains help_text fidelity."""
    collection: Collection = read_collection_file(GOOGLE_DRIVE_COLLECTION_PATH)
    token_var = next(
        (v for v in collection.variables if v.name == "google_drive_access_token"),
        None,
    )
    assert token_var is not None, "google_drive_access_token variable not found in collection"
    assert token_var.help_text is not None, (
        "CollectionVariable.help_text must not be None for google_drive_access_token"
    )
    assert token_var.help_text.strip(), (
        "CollectionVariable.help_text must be non-empty for google_drive_access_token"
    )
    assert "Google Cloud Console" in token_var.help_text
    assert "OAuth consent" in token_var.help_text
    assert "Credentials" in token_var.help_text
    assert "https://www.googleapis.com/auth/drive" in token_var.help_text

    # Round-trip model serialization
    dumped = token_var.model_dump()
    assert dumped.get("help_text") == token_var.help_text
    reloaded = CollectionVariable(**dumped)
    assert reloaded.help_text == token_var.help_text


@pytest.mark.timeout(30)
@pytest.mark.usefixtures("qapp")
def test_variable_guidance_card_initialization_from_reference_collection() -> None:
    """VariableGuidanceCard initializes guidance panel and secret masking for token."""
    collection: Collection = read_collection_file(GOOGLE_DRIVE_COLLECTION_PATH)
    token_var = next(
        (v for v in collection.variables if v.name == "google_drive_access_token"),
        None,
    )
    assert token_var is not None, "google_drive_access_token variable not found"

    card = VariableGuidanceCard(token_var)
    try:
        # Guidance toggle and container
        assert card.guidance_toggle_button is not None, (
            "VariableGuidanceCard must create guidance toggle button when help_text is present"
        )
        assert card.guidance_toggle_button.text() == "Show Guidance"
        assert card.guidance_container is not None, (
            "VariableGuidanceCard must create guidance container when help_text is present"
        )
        assert card.guidance_container.isVisible() is False

        # Toggle guidance expansion
        card.toggle_guidance()
        assert card.guidance_container.isVisible() is True
        assert card.guidance_toggle_button.text() == "Hide Guidance"

        card.toggle_guidance()
        assert card.guidance_container.isVisible() is False
        assert card.guidance_toggle_button.text() == "Show Guidance"

        # Secret masking and eye toggle
        assert card.input_field.echoMode() == QLineEdit.EchoMode.Password
        assert card.secret_toggle_button is not None
        assert card.secret_toggle_button.text() == "Show"

        card.toggle_secret_visibility()
        assert card.input_field.echoMode() == QLineEdit.EchoMode.Normal
        assert card.secret_toggle_button.text() == "Hide"

        card.toggle_secret_visibility()
        assert card.input_field.echoMode() == QLineEdit.EchoMode.Password
        assert card.secret_toggle_button.text() == "Show"
    finally:
        card.close()


@pytest.mark.timeout(30)
@pytest.mark.usefixtures("qapp")
def test_variable_setup_wizard_loads_reference_collection() -> None:
    """VariableSetupWizardDialog loads all reference variables and partitions correctly."""
    collection: Collection = read_collection_file(GOOGLE_DRIVE_COLLECTION_PATH)
    dialog = VariableSetupWizardDialog(
        variables=collection.variables,
        collection_name=collection.name,
    )
    try:
        assert len(dialog.cards) == len(collection.variables)

        # Card for google_drive_access_token has guidance initialized
        token_card = dialog._cards_by_name.get("google_drive_access_token")
        assert token_card is not None, "Card for google_drive_access_token missing"
        assert token_card.guidance_container is not None, (
            "google_drive_access_token card must have guidance_container initialized"
        )

        # Secret partitioning
        partitioned = dialog.get_configured_variables()
        assert "google_drive_access_token" in partitioned["secrets"]
        assert "google_drive_base_url" in partitioned["overrides"]
    finally:
        dialog.close()


@pytest.mark.timeout(30)
@pytest.mark.usefixtures("qapp")
def test_backward_compatibility_with_minimal_variables() -> None:
    """Variables lacking help_text parse cleanly and cards omit guidance toggles."""
    minimal_var = CollectionVariable(
        name="legacy_endpoint",
        type="string",
        default="https://api.example.com",
        description="Legacy endpoint",
    )
    assert minimal_var.help_text is None

    card = VariableGuidanceCard(minimal_var)
    try:
        assert card.guidance_toggle_button is None
        assert card.guidance_container is None
        assert card.is_valid() is True
    finally:
        card.close()

    wizard = VariableSetupWizardDialog(variables=[minimal_var])
    try:
        assert len(wizard.cards) == 1
        partitioned = wizard.get_configured_variables()
        assert "legacy_endpoint" in partitioned["overrides"]
    finally:
        wizard.close()
