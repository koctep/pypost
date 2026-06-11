"""JSON body validation."""

import json

from PySide6.QtGui import QTextDocument

from pypost.ui.widgets.validate.validation_error import ValidationError


class JsonBodyValidator:
    def validate(self, document: QTextDocument) -> list[ValidationError]:
        text = document.toPlainText()
        if not text.strip():
            return []

        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            return [
                ValidationError(
                    line=exc.lineno,
                    column=exc.colno,
                    message=exc.msg,
                )
            ]
        return []
