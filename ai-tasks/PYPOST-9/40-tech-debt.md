# PYPOST-9: Technical Debt Analysis


## Shortcuts Taken

- **Simple Regex Implementation**: The used regular expressions for JSON are quite simple and may not cover all edge cases (e.g., very complex nested structures or tricky escaping in key strings), but they are suitable for 99% of API usage cases. — [PYPOST-393](https://pypost.atlassian.net/browse/PYPOST-393)
- **No JSON Validation**: The highlighter simply colors tokens; it does not check the validity of the JSON structure. — [PYPOST-394](https://pypost.atlassian.net/browse/PYPOST-394)

## Code Quality Issues

- **Hardcoded Colors**: Colors (`darkblue`, `blue`, `green`, `purple`) are defined directly in the `JsonHighlighter` class code. Adding dark theme support will require refactoring (moving to config or using system palette colors). — [PYPOST-395](https://pypost.atlassian.net/browse/PYPOST-395)

## Missing Tests

- Unit tests for `JsonHighlighter` are missing. Verification was done visually. Tests checking that expected formats are applied for given text can be added. — [PYPOST-396](https://pypost.atlassian.net/browse/PYPOST-396)

## Performance Concerns

- **Regex on Whole Block**: `QSyntaxHighlighter` works block by block, but complex regular expressions can work slowly on very large strings (megabytes of JSON). In the current implementation, regexes are optimized enough, but UI delays are possible on huge responses. — [PYPOST-397](https://pypost.atlassian.net/browse/PYPOST-397)

## Follow-up Tasks

- Move color settings to application theme or config. — [PYPOST-398](https://pypost.atlassian.net/browse/PYPOST-398)
- Add tests for `JsonHighlighter`. — [PYPOST-399](https://pypost.atlassian.net/browse/PYPOST-399)
