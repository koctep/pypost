from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

from pypost.core.template_expression_tokenizer import TEMPLATE_PLACEHOLDER_PATTERN


class JsonHighlighter(QSyntaxHighlighter):
    """Highlighter for JSON syntax and template placeholders."""

    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("darkblue"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ["true", "false", "null"]
        for word in keywords:
            pattern = QRegularExpression(f"\\b{word}\\b")
            self.rules.append((pattern, keyword_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("blue"))
        self.rules.append(
            (QRegularExpression(r"\b-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\b"), number_format)
        )

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("green"))
        self.rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))

        key_format = QTextCharFormat()
        key_format.setForeground(QColor("purple"))
        self.key_rule = (QRegularExpression(r'("[^"\\]*(\\.[^"\\]*)*")\s*:'), key_format)

        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor("darkorange"))
        variable_format.setFontWeight(QFont.Bold)
        self.variable_format = variable_format

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
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
