# Templating

PyPost substitutes placeholders in URL, header names/values, param names/values, and
body before sending a request. Syntax is Jinja2-style: `{{ name }}`.

## Environment variables

If the active environment defines `host` = `https://api.example.com`, then:

```text
{{ host }}/users
```

becomes `https://api.example.com/users` at send time (and when copying cURL from the
editor).

Hover a `{{ ... }}` placeholder in the editor to preview the resolved value. Hidden
variables stay masked as `********`.

## Template functions

You can call allow-listed functions inside placeholders. Only these names are
permitted:

| Function | Purpose | Example |
| -------- | ------- | ------- |
| `urlencode` | URL-encode a value | `{{ urlencode(query) }}` |
| `md5` | MD5 hex digest | `{{ md5(secret) }}` |
| `base64` | Base64-encode | `{{ base64(payload) }}` |

Nested allow-listed calls are allowed, for example:

```text
{{ md5(urlencode(db)) }}
```

Arguments may be environment variable names or nested function results. Arbitrary
Python or unknown function names are not allowed.

## Invalid or unresolved expressions

If a function expression is invalid, a variable is missing, or rendering fails, PyPost
falls back to the **original** placeholder text (it may be sent unresolved). Prefer
testing the request in the GUI before exposing it as an MCP tool.

## MCP request parameters

Placeholders of the form `{{ mcp.request.param_name }}` are **not** environment
variables. They become inputs that an AI agent supplies when calling the tool. See
[MCP Tools for AI Agents](mcp-tools.md).
