import json
from typing import Any

import yaml


class YamlBodyConversionError(Exception):
    """YAML body could not be parsed for JSON send."""


def convert_yaml_body_to_object(text: str) -> Any:
    """Parse YAML text into a JSON-serializable Python object.

    Raises:
        YamlBodyConversionError: On empty/invalid YAML or non-serializable result.
    """
    stripped = text.strip()
    if not stripped:
        raise YamlBodyConversionError("YAML body is empty.")

    try:
        documents = list(yaml.safe_load_all(stripped))
    except yaml.YAMLError as exc:
        raise YamlBodyConversionError(str(exc)) from exc

    if len(documents) != 1:
        raise YamlBodyConversionError(
            f"Expected exactly one YAML document, found {len(documents)}."
        )

    parsed = documents[0]
    if parsed is None:
        raise YamlBodyConversionError("YAML document is empty.")

    try:
        json.dumps(parsed)
    except (TypeError, ValueError) as exc:
        raise YamlBodyConversionError(f"Parsed YAML is not JSON-serializable: {exc}") from exc

    return parsed
