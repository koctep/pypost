from __future__ import annotations

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

from pypost.core.template_expression_tokenizer import TEMPLATE_PLACEHOLDER_PATTERN
from pypost.ui.theme.json_syntax_theme import JsonSyntaxColors, resolve_json_syntax_colors

# Minified JSON can occupy a single QTextBlock; skip regex highlighting above this size
# to avoid UI stalls on megabyte-scale lines.
MAX_HIGHLIGHT_BLOCK_CHARS = 32_768


class JsonHighlighter(QSyntaxHighlighter):
    """Highlighter for JSON syntax and template placeholders.

    Uses ``QRegularExpression`` rules (not a JSON parser) for approximate token coloring
    on each ``QTextDocument`` block. This is intentional: ``QSyntaxHighlighter`` runs
    per block without AST context, and regex rules are fast enough for typical API
    payloads.

    Known limitations (accepted for coloring-only use):

    - Strings or keys split across line boundaries are not merged across blocks.
    - Escape sequences inside strings use a simple pattern; unusual escapes may
      miscolor trailing characters.
    - Object keys are detected by ``"..."\\s*:`` on the same line.
    - The number rule targets common literals; spec edge cases such as leading zeros
      or non-finite values may not match exactly.
    - Blocks longer than ``MAX_HIGHLIGHT_BLOCK_CHARS`` skip highlighting entirely so
      minified megabyte JSON on one line does not block the UI thread.

    Structural JSON validation is handled by ``ValidationController`` in the body editor;
    see ``doc/dev/body_editor_validation.md``. Coloring-only scope is documented in
    ``doc/dev/json_syntax_highlighting.md``.
    """

    def __init__(self, document, colors: JsonSyntaxColors | None = None):
        super().__init__(document)
        self._colors = colors or resolve_json_syntax_colors()
        self._build_rules()

    def set_colors(self, colors: JsonSyntaxColors) -> None:
        """Rebind token colors and re-highlight the document."""
        self._colors = colors
        self._build_rules()
        self.rehighlight()

    def _build_rules(self) -> None:
        self.rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(self._colors.keyword))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ["true", "false", "null"]
        for word in keywords:
            pattern = QRegularExpression(f"\\b{word}\\b")
            self.rules.append((pattern, keyword_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor(self._colors.number))
        self.rules.append(
            (QRegularExpression(r"\b-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\b"), number_format)
        )

        string_format = QTextCharFormat()
        string_format.setForeground(QColor(self._colors.string))
        self.rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))

        key_format = QTextCharFormat()
        key_format.setForeground(QColor(self._colors.key))
        self.key_rule = (QRegularExpression(r'("[^"\\]*(\\.[^"\\]*)*")\s*:'), key_format)

        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor(self._colors.placeholder))
        variable_format.setFontWeight(QFont.Bold)
        self.variable_format = variable_format

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
        if len(text) > MAX_HIGHLIGHT_BLOCK_CHARS:
            return

        for pattern, fmt in self.rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        pattern, fmt = self.key_rule
        iterator = pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            self.setFormat(match.capturedStart(1), match.capturedLength(1), fmt)

        for match in TEMPLATE_PLACEHOLDER_PATTERN.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.variable_format)
