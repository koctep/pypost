from dataclasses import dataclass


@dataclass(frozen=True)
class JsonSyntaxColors:
    """Foreground color names for JsonHighlighter token classes."""

    keyword: str = "darkblue"
    number: str = "blue"
    string: str = "green"
    key: str = "purple"
    placeholder: str = "darkorange"


DEFAULT_JSON_SYNTAX_COLORS = JsonSyntaxColors()
