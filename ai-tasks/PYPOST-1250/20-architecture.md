# PYPOST-1250: Test Architecture

The new test module exercises the public `TemplateService` rendering APIs. It uses real
`FunctionRegistry`, resolver, and Jinja integration so nesting, lexical scanning, validation,
and strict fallback behavior are tested together.

The cases are intentionally isolated from GUI and external services. The test suite records
the current compatibility contract: valid expressions inside Jinja comments are not evaluated,
while malformed strict expressions remain fail-closed during strict rendering.
