"""Body validator protocol and format registry."""

from __future__ import annotations


from typing import Protocol

from PySide6.QtGui import QTextDocument

from pypost.ui.widgets.fold.fold_region import BodyFormat
from pypost.ui.widgets.validate.json_body_validator import JsonBodyValidator
from pypost.ui.widgets.validate.validation_error import ValidationError
from pypost.ui.widgets.validate.xml_body_validator import XmlBodyValidator
from pypost.ui.widgets.validate.yaml_body_validator import YamlBodyValidator


class BodyValidator(Protocol):
    def validate(self, document: QTextDocument) -> list[ValidationError]:
        ...


_VALIDATORS: dict[BodyFormat, BodyValidator] = {
    BodyFormat.JSON: JsonBodyValidator(),
    BodyFormat.YAML: YamlBodyValidator(),
    BodyFormat.XML: XmlBodyValidator(),
}


def get_validator(body_format: BodyFormat) -> BodyValidator:
    if body_format is BodyFormat.PLAIN:
        return _PlainValidator()
    return _VALIDATORS[body_format]


class _PlainValidator:
    def validate(self, document: QTextDocument) -> list[ValidationError]:
        return []
