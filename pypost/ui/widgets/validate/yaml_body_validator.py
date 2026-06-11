"""YAML body validation."""

import yaml
from PySide6.QtGui import QTextDocument

from pypost.ui.widgets.validate.validation_error import ValidationError


class YamlBodyValidator:
    def validate(self, document: QTextDocument) -> list[ValidationError]:
        text = document.toPlainText()
        if not text.strip():
            return []

        try:
            list(yaml.safe_load_all(text))
        except yaml.YAMLError as exc:
            mark = exc.problem_mark
            if mark is None:
                return [
                    ValidationError(
                        line=1,
                        column=1,
                        message=str(exc.problem or exc),
                    )
                ]
            return [
                ValidationError(
                    line=mark.line + 1,
                    column=mark.column + 1,
                    message=str(exc.problem or exc),
                )
            ]
        return []
