from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import QRegularExpression

class JsonHighlighter(QSyntaxHighlighter):
    """Highlighter for JSON syntax."""

    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        # Keywords (true, false, null)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("darkblue"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ["true", "false", "null"]
        for word in keywords:
            pattern = QRegularExpression(f"\\b{word}\\b")
            self.rules.append((pattern, keyword_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("blue"))
        self.rules.append((QRegularExpression(r"\b-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\b"), number_format))

        # Strings (values)
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("green"))
        # Match strings but be careful about context. This matches any string.
        # We will handle keys separately or rely on order.
        self.rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))

        # Keys (strings followed by colon)
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("purple")) # or dark magenta
        # Regex for key: "string" followed by optional space then :
        # Lookahead for colon is tricky in single regex if we want to color only the string.
        # We can iterate matches and check context, or use a specific regex that matches the key part.
        
        # In QSyntaxHighlighter, we iterate over text.
        # Let's try to match keys specifically.
        # A key is a string followed by :
        # But we need to color ONLY the string part as key, not the colon.
        # QRegularExpression does not support variable length lookbehind easily for this in simple rule loop?
        # Actually we can just match the whole "key": pattern and only color the "key" part?
        # But highlightBlock applies format to the length of match usually.
        
        # Better approach for Keys:
        # Match "key"\s*:
        # We can use a capturing group for the key part if we implemented custom loop,
        # but the standard loop below uses match.capturedStart() / length().
        
        # Let's stick to simple rules first.
        # If we put the Key rule AFTER String rule, does it overwrite? Yes.
        
        # Regex for key: "([^"\\]*(\\.[^"\\]*)*)"\s*:
        self.key_rule = (QRegularExpression(r'"([^"\\]*(\\.[^"\\]*)*)"\s*:'), key_format)


    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
        
        # Apply standard rules (keywords, numbers, strings)
        for pattern, fmt in self.rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        # Apply Key rule separately to handle the colon exclusion
        pattern, fmt = self.key_rule
        iterator = pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            # match.captured(1) is the string content without quotes? 
            # No, our regex includes quotes in group 1 if we did: "..."
            # Let's adjust regex:
            # "([^"\\]*(\\.[^"\\]*)*)"\s*:
            # Group 0 is full match: "key":
            # We want to format "key" (including quotes).
            
            # Actually, let's just match the part we want to color?
            # But we need the context of the colon to know it is a key.
            
            # So we match the full "key": and then only format the part before the colon.
            
            # Find the position of the colon in the match to know where to stop formatting?
            # Or just use the length of the captured group 1 if we capture the string including quotes.
            
            # Let's try:
            # r'("[^"\\]*(\\.[^"\\]*)*")\s*:'
            # Group 1 is the string with quotes.
            
            # Re-defining regex inside loop for clarity or use class member
            pass

        # Re-implementation of Key highlighting with correct logic
        key_pattern = QRegularExpression(r'("[^"\\]*(\\.[^"\\]*)*")\s*:')
        iterator = key_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            # Apply format only to the first capturing group (the string with quotes)
            self.setFormat(match.capturedStart(1), match.capturedLength(1), self.key_rule[1])


