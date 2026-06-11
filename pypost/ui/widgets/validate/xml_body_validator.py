"""XML body validation (stub until PYPOST-513 enables XML format)."""

from PySide6.QtGui import QTextDocument

from pypost.ui.widgets.validate.validation_error import ValidationError


class XmlBodyValidator:
    def validate(self, document: QTextDocument) -> list[ValidationError]:
        return []
