# PYPOST-11: Technical Debt Analysis


## Shortcuts Taken

- **Simple Regex Implementation**: The used regular expressions for JSON are quite simple and may not cover all edge cases (e.g., very complex nested structures or tricky escaping in key strings), but they are suitable for 99% of API usage cases. — [PYPOST-97](https://pypost.atlassian.net/browse/PYPOST-97)
- **No JSON Validation**: The highlighter simply colors tokens; it does not check the validity of the JSON structure. — [PYPOST-98](https://pypost.atlassian.net/browse/PYPOST-98)

## Code Quality Issues

- **Hardcoded Colors**: Colors (`darkblue`, `blue`, `green`, `purple`) are defined directly in the `JsonHighlighter` class code. Adding dark theme support will require refactoring (moving to config or using system palette colors). — [PYPOST-99](https://pypost.atlassian.net/browse/PYPOST-99)

## Missing Tests

- Unit tests for `JsonHighlighter` are missing. Verification was done visually. Tests checking that expected formats are applied for given text can be added. — [PYPOST-100](https://pypost.atlassian.net/browse/PYPOST-100)

## Performance Concerns

- **Regex on Whole Block**: `QSyntaxHighlighter` works block by block, but complex regular expressions can work slowly on very large strings (megabytes of JSON). In the current implementation, regexes are optimized enough, but UI delays are possible on huge responses. — [PYPOST-101](https://pypost.atlassian.net/browse/PYPOST-101)

## Follow-up Tasks

- Move color settings to application theme or config. — [PYPOST-102](https://pypost.atlassian.net/browse/PYPOST-102)
- Add tests for `JsonHighlighter`. — [PYPOST-103](https://pypost.atlassian.net/browse/PYPOST-103)
