"""Variable setup wizard dialog and guidance card components (PYPOST-1373).

Provides:
- VariableGuidanceCard: A reusable QFrame widget presenting an individual
  collection variable with masking toggles, expandable rich guidance, and
  inline validation feedback.
- VariableSetupWizardDialog: A modal QDialog guiding users through configuring
  required and optional collection variables.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from pypost.models.collection_variable import CollectionVariable
from pypost.ui.widget_ids import (
    VARIABLE_GUIDANCE_CARD,
    VARIABLE_GUIDANCE_EXPAND_BUTTON,
    VARIABLE_GUIDANCE_SECRET_TOGGLE,
    VARIABLE_SETUP_APPLY_BUTTON,
    VARIABLE_SETUP_CANCEL_BUTTON,
    VARIABLE_SETUP_WIZARD_DIALOG,
    set_widget_id,
)

logger = logging.getLogger(__name__)


class _GuidanceContainer(QFrame):
    """Container frame for guidance panel with tracked visibility for headless testing."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._explicit_visible: bool = False

    def setVisible(self, visible: bool) -> None:
        self._explicit_visible = visible
        super().setVisible(visible)

    def isVisible(self) -> bool:
        parent = self.parentWidget()
        if parent is not None and not parent.isVisible():
            return self._explicit_visible
        return super().isVisible()


class VariableGuidanceCard(QFrame):
    """Card widget rendering input, guidance, and validation for a CollectionVariable."""

    def __init__(
        self,
        variable: CollectionVariable,
        initial_value: Optional[Any] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._variable = variable
        set_widget_id(self, VARIABLE_GUIDANCE_CARD)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 10, 12, 10)
        self._layout.setSpacing(6)

        # Header Row: Name, Type Badge, Required Asterisk / Badge
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.name_label = QLabel(variable.name, self)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        header_layout.addWidget(self.name_label)

        type_text = f"[{variable.type}]"
        self.type_badge = QLabel(type_text, self)
        self.type_badge.setStyleSheet(
            "color: #888888; font-size: 11px; font-family: monospace;"
        )
        header_layout.addWidget(self.type_badge)

        if variable.required:
            self.required_badge = QLabel("* Required", self)
            self.required_badge.setStyleSheet(
                "color: #e74c3c; font-weight: bold; font-size: 11px;"
            )
            header_layout.addWidget(self.required_badge)

        header_layout.addStretch()

        if variable.description:
            desc_label = QLabel(variable.description, self)
            desc_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
            header_layout.addWidget(desc_label)

        self._layout.addLayout(header_layout)

        # Input Row: QLineEdit + optional secret toggle button
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)

        self.input_field = QLineEdit(self)
        self._input_field = self.input_field  # alias for tests

        # Pre-populate value
        if initial_value is not None:
            self.input_field.setText(str(initial_value))
        elif variable.default is not None:
            self.input_field.setText(str(variable.default))
        else:
            self.input_field.setText("")

        self.secret_toggle_button: Optional[QToolButton] = None
        self._secret_toggle_btn: Optional[QToolButton] = None

        if variable.secret:
            self.input_field.setEchoMode(QLineEdit.EchoMode.Password)
            self.secret_toggle_button = QToolButton(self)
            self._secret_toggle_btn = self.secret_toggle_button
            set_widget_id(self.secret_toggle_button, VARIABLE_GUIDANCE_SECRET_TOGGLE)
            self.secret_toggle_button.setText("Show")
            self.secret_toggle_button.setToolTip("Toggle password visibility")
            self.secret_toggle_button.clicked.connect(self.toggle_secret_visibility)
            input_layout.addWidget(self.input_field)
            input_layout.addWidget(self.secret_toggle_button)
        else:
            input_layout.addWidget(self.input_field)

        self._layout.addLayout(input_layout)

        # Inline error label
        self.error_label = QLabel("", self)
        self._error_label = self.error_label  # alias for tests
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 11px;")
        self.error_label.setVisible(False)
        self._layout.addWidget(self.error_label)

        # Guidance toggle and expandable panel
        self.guidance_toggle_button: Optional[QPushButton] = None
        self._guidance_toggle_btn: Optional[QPushButton] = None
        self.guidance_container: Optional[QFrame] = None
        self._guidance_container: Optional[QFrame] = None

        if variable.help_text:
            guidance_row = QHBoxLayout()
            self.guidance_toggle_button = QPushButton("Show Guidance", self)
            self._guidance_toggle_btn = self.guidance_toggle_button
            set_widget_id(
                self.guidance_toggle_button, VARIABLE_GUIDANCE_EXPAND_BUTTON
            )
            self.guidance_toggle_button.setStyleSheet(
                "text-align: left; padding: 2px 4px; font-size: 11px;"
            )
            self.guidance_toggle_button.clicked.connect(self.toggle_guidance)
            guidance_row.addWidget(self.guidance_toggle_button)
            guidance_row.addStretch()
            self._layout.addLayout(guidance_row)

            # Collapsible guidance container
            self.guidance_container = _GuidanceContainer(self)
            self._guidance_container = self.guidance_container
            self.guidance_container.setFrameShape(QFrame.Shape.Box)
            self.guidance_container.setStyleSheet(
                "background-color: rgba(255, 255, 255, 0.05); border-radius: 4px; padding: 6px;"
            )
            guidance_layout = QVBoxLayout(self.guidance_container)
            guidance_layout.setContentsMargins(8, 8, 8, 8)

            guidance_text = QLabel(variable.help_text, self.guidance_container)
            guidance_text.setTextFormat(Qt.TextFormat.RichText)
            guidance_text.setWordWrap(True)
            guidance_text.setOpenExternalLinks(True)
            guidance_text.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextBrowserInteraction
            )
            guidance_layout.addWidget(guidance_text)

            self.guidance_container.setVisible(False)
            self._layout.addWidget(self.guidance_container)

        # Connect textChanged to clear error
        self.input_field.textChanged.connect(self._on_text_changed)

    @property
    def variable(self) -> CollectionVariable:
        """Return the associated CollectionVariable definition."""
        return self._variable

    def get_value(self) -> str:
        """Return the current string input value."""
        return self.input_field.text()

    def set_value(self, value: Any) -> None:
        """Set the input field value."""
        text = "" if value is None else str(value)
        self.input_field.setText(text)

    def is_valid(self) -> bool:
        """Check whether the card satisfies validation requirements."""
        val = self.get_value().strip()
        if self._variable.required and not val:
            return False
        return True

    def set_validation_error(self, message: Optional[str] = None) -> None:
        """Display or clear inline validation error."""
        if message:
            self.error_label.setText(message)
            self.error_label.setVisible(True)
            self.input_field.setStyleSheet(
                "QLineEdit { border: 1px solid #e74c3c; }"
            )
        else:
            self.error_label.setText("")
            self.error_label.setVisible(False)
            self.input_field.setStyleSheet("")

    def toggle_guidance(self, expanded: Optional[bool] = None) -> None:
        """Toggle guidance panel expansion state."""
        if not self.guidance_container or not self.guidance_toggle_button:
            return

        if expanded is not None:
            new_state = expanded
        else:
            new_state = self.guidance_container.isHidden()

        self.guidance_container.setVisible(new_state)
        self.guidance_toggle_button.setText(
            "Hide Guidance" if new_state else "Show Guidance"
        )

    def toggle_secret_visibility(self) -> None:
        """Toggle EchoMode between Password and Normal for secret variables."""
        if not self._variable.secret:
            return

        if self.input_field.echoMode() == QLineEdit.EchoMode.Password:
            self.input_field.setEchoMode(QLineEdit.EchoMode.Normal)
            if self.secret_toggle_button:
                self.secret_toggle_button.setText("Hide")
        else:
            self.input_field.setEchoMode(QLineEdit.EchoMode.Password)
            if self.secret_toggle_button:
                self.secret_toggle_button.setText("Show")

    def _on_text_changed(self) -> None:
        """Clear error highlight as user types."""
        if self.error_label.isVisible():
            self.set_validation_error(None)


class VariableSetupWizardDialog(QDialog):
    """Modal dialog guiding users through configuring collection variables."""

    def __init__(
        self,
        variables: list[CollectionVariable],
        initial_values: Optional[dict[str, Any]] = None,
        collection_name: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._variables = list(variables)
        self._initial_values = initial_values or {}
        self._collection_name = collection_name
        set_widget_id(self, VARIABLE_SETUP_WIZARD_DIALOG)

        title = (
            f"Configure Variables — {collection_name}"
            if collection_name
            else "Configure Collection Variables"
        )
        self.setWindowTitle(title)
        self.resize(560, 500)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header intro
        intro_layout = QVBoxLayout()
        header_title = QLabel(
            f"Setup Variables for {collection_name}"
            if collection_name
            else "Setup Variables",
            self,
        )
        header_title.setStyleSheet("font-size: 15px; font-weight: bold;")
        intro_layout.addWidget(header_title)

        header_subtitle = QLabel(
            "Please configure the following environment variables required by this collection. "
            "Sensitive credentials are kept masked.",
            self,
        )
        header_subtitle.setWordWrap(True)
        header_subtitle.setStyleSheet("color: #888888; font-size: 12px;")
        intro_layout.addWidget(header_subtitle)
        main_layout.addLayout(intro_layout)

        # Scroll area containing variable cards
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        self._cards_layout = QVBoxLayout(scroll_content)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(10)

        self._cards: list[VariableGuidanceCard] = []
        self._cards_by_name: dict[str, VariableGuidanceCard] = {}

        if not self._variables:
            no_vars_label = QLabel(
                "No variables required for this collection.", scroll_content
            )
            no_vars_label.setStyleSheet("color: #888888; font-style: italic; padding: 20px;")
            self._cards_layout.addWidget(no_vars_label)
        else:
            for var in self._variables:
                init_val = self._initial_values.get(var.name)
                card = VariableGuidanceCard(var, initial_value=init_val, parent=scroll_content)
                self._cards.append(card)
                self._cards_by_name[var.name] = card
                self._cards_layout.addWidget(card)

        self._cards_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # Dialog Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        self.apply_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        if self.apply_button:
            self.apply_button.setText("Save")
            set_widget_id(self.apply_button, VARIABLE_SETUP_APPLY_BUTTON)

        self.cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if self.cancel_button:
            set_widget_id(self.cancel_button, VARIABLE_SETUP_CANCEL_BUTTON)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    @property
    def cards(self) -> list[VariableGuidanceCard]:
        """Return the list of variable cards."""
        return self._cards

    def validate_all(self) -> bool:
        """Validate all cards. Updates visual error indicators if invalid."""
        all_valid = True
        for card in self._cards:
            if not card.is_valid():
                card.set_validation_error("This variable is required")
                all_valid = False
            else:
                card.set_validation_error(None)
        return all_valid

    def accept(self) -> None:
        """Validate inputs before accepting dialog."""
        if not self.validate_all():
            return
        super().accept()

    def get_values(self) -> dict[str, Any]:
        """Return a mapping of variable name to user-entered value."""
        values: dict[str, Any] = {}
        for card in self._cards:
            val = card.get_value()
            # If the variable was an integer/number, cast if appropriate
            if card.variable.type == "integer":
                try:
                    values[card.variable.name] = int(val)
                    continue
                except (ValueError, TypeError):
                    pass
            elif card.variable.type == "number":
                try:
                    values[card.variable.name] = float(val)
                    continue
                except (ValueError, TypeError):
                    pass
            values[card.variable.name] = val
        return values

    def get_configured_variables(self) -> dict[str, dict[str, Any]]:
        """Return variables partitioned into 'overrides' and 'secrets'."""
        overrides: dict[str, Any] = {}
        secrets: dict[str, Any] = {}

        values = self.get_values()
        for card in self._cards:
            name = card.variable.name
            val = values.get(name)
            if card.variable.secret:
                secrets[name] = val
            else:
                overrides[name] = val

        return {
            "values": values,
            "overrides": overrides,
            "secrets": secrets,
        }
