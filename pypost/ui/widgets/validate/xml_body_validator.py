"""XML body validation."""

import xml.etree.ElementTree as ET

from PySide6.QtGui import QTextDocument

from pypost.ui.widgets.validate.validation_error import ValidationError


class XmlBodyValidator:
    def validate(self, document: QTextDocument) -> list[ValidationError]:
        text = document.toPlainText()
        if not text.strip():
            return []

        try:
            ET.fromstring(text)
        except ET.ParseError as exc:
            line, column = exc.position
            return [
                ValidationError(
                    line=line,
                    column=column,
                    message=str(exc),
                )
            ]
        return []
