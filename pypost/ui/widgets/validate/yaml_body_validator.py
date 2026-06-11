"""YAML body validation (stub until PYPOST-513 enables YAML format)."""

from PySide6.QtGui import QTextDocument

from pypost.ui.widgets.validate.validation_error import ValidationError


class YamlBodyValidator:
    def validate(self, document: QTextDocument) -> list[ValidationError]:
        return []
