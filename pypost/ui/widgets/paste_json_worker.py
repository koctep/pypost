import json
import logging

from PySide6.QtCore import QThread, Signal

from pypost.core.yaml_json_converter import convert_json_object_to_yaml
from pypost.ui.widgets.fold import BodyFormat

logger = logging.getLogger(__name__)


class PasteJsonFormatWorker(QThread):
    """Parse and format pasted JSON off the UI thread."""

    finished_with_result = Signal(int, object)

    def __init__(
        self,
        generation_id: int,
        text: str,
        *,
        indent_size: int,
        body_format: BodyFormat,
        yaml_as_json: bool,
    ) -> None:
        super().__init__()
        self._generation_id = generation_id
        self._text = text
        self._indent_size = indent_size
        self._body_format = body_format
        self._yaml_as_json = yaml_as_json

    def run(self) -> None:
        logger.debug(
            "paste_json_worker_run_started generation=%d chars=%d",
            self._generation_id,
            len(self._text),
        )
        try:
            parsed = json.loads(self._text)
            if self._body_format == BodyFormat.YAML and self._yaml_as_json:
                formatted = convert_json_object_to_yaml(parsed).rstrip("\n")
            else:
                formatted = json.dumps(parsed, indent=self._indent_size)
            logger.debug(
                "paste_json_worker_run_completed generation=%d formatted=True",
                self._generation_id,
            )
            self.finished_with_result.emit(self._generation_id, formatted)
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.debug(
                "paste_json_worker_run_completed generation=%d formatted=False",
                self._generation_id,
            )
            self.finished_with_result.emit(self._generation_id, None)
