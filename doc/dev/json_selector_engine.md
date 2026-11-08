# Unified JSON Selector Path Evaluation Engine (PYPOST-1394)

## Overview

The **Unified JSON Selector Path Evaluation Engine** (`JsonSelectorEngine`) provides a consolidated,
high-performance path evaluation and AST traversal engine for masking sensitive response data
across PyPost subsystems.

Modern API workflows handle sensitive data such as API tokens, credentials, passwords, session
keys, and PII. PyPost supports masking configured sensitive response keys across two distinct
runtime boundaries:
1. **MCP Egress Redaction (`SensitiveTextSanitizer`)**: Irreversibly replaces configured sensitive
   keys with `***` in JSON responses returned to AI coding agents via Model Context Protocol tools.
2. **Interactive GUI Presentation (`ResponseMaskController`)**: Reversibly formats response JSON
   with `"***"` placeholders in `ResponseView`, tracking precise token character offsets
   (`MaskedTokenSpan`) to enable interactive click-to-reveal inspection for human developers.

Prior to PYPOST-1394, both consumers independently maintained recursive JSON traversal, path
string generation, and wildcard matching logic. `JsonSelectorEngine` consolidates this shared
logic into a domain engine located in `pypost/core/json_selector_engine.py` with zero UI
dependencies, optimized $O(1)$ bare key lookup partitioning, and AST-based path evaluation.

---

## Architecture

The unified engine is built around two primary classes in `pypost/core/json_selector_engine.py`:

```
+--------------------------------------------------------------+
|                     RequestData                              |
|           (hidden_response_fields: list[str])                |
+------------------------------+-------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|                    JsonSelectorEngine                        |
|                                                              |
|   +--------------------------+  +--------------------------+ |
|   |   _bare_keys (set[str])  |  | _path_selectors (list)   | |
|   |   e.g. {'token', 'ssn'}  |  | CompiledPathSelector     | |
|   |   $O(1)$ direct lookup   |  | e.g. items.*.secret      | |
|   +--------------------------+  +--------------------------+ |
|                                                              |
|   - matches(path, key) -> bool                               |
|   - redact_tree(node, placeholder) -> (redacted, count)      |
+------------------------------+-------------------------------+
            |                                      |
            v                                      v
+-----------------------+              +-----------------------+
| SensitiveTextSanitizer|              | ResponseMaskController|
| (MCP irreversible)    |              | (GUI click-to-reveal) |
+-----------------------+              +-----------------------+
```

### Components

- **`CompiledPathSelector`**:
  Parses hierarchical path strings (such as `user.profile.token` or `items[*].secret`) into
  normalized token tuples (`('items', '*', 'secret')`). Evaluates candidate path tokens in linear
  time with wildcard support (`*` matches any object key or array index).
- **`JsonSelectorEngine`**:
  The central facade that normalizes and compiles raw selector strings, partitions them into
  fast bare keys and compiled path selectors, determines whether an AST node matches, and executes
  immutable tree redaction.
- **`SensitiveTextSanitizer` Integration**:
  MCP response redaction delegates `redact_json_response_fields()` directly to
  `JsonSelectorEngine.redact_tree()`, returning a sanitized deep-copy tree and serialization.
- **`ResponseMaskController` (`JsonMaskFormatter`) Integration**:
  Interactive GUI formatting instantiates `JsonSelectorEngine` to query `engine.matches(path, key)`
  during streaming token formatting, recording character offset spans with an incremental $O(1)$
  offset counter.

---

## Supported Selector Syntax

Selectors configured in `RequestData.hidden_response_fields` support the following syntax:

| Selector Pattern | Example | Semantics |
| :--- | :--- | :--- |
| **Bare Field Name** | `token`, `password`, `ssn` | Matches the field name at **any** level or depth in the JSON hierarchy. |
| **Dotted Object Path** | `user.credentials.apiKey` | Matches **only** when the exact hierarchy of parent keys matches from document root. |
| **Array Bracket Wildcard** | `items[*].secret`, `[*].id` | Matches elements within arrays at the specified position in the hierarchy. |
| **Array Dot Wildcard** | `items.*.secret`, `*.id` | Alternative wildcard notation equivalent to bracket wildcard notation. |
| **Nested Array Wildcards** | `matrix[*][*].value` | Matches elements inside multi-dimensional nested arrays. |
| **Header Selectors** | `header:Authorization` | Applies exclusively to HTTP response headers. Automatically ignored by JSON body evaluation. |

---

## API & Usage

### 1. `JsonSelectorEngine`

Located in `pypost.core.json_selector_engine`.

#### `__init__(selectors: Iterable[str] | None = None)`
Initializes the engine and compiles the given selector rules. Blank entries, whitespace, and
non-body selectors (e.g. `header:*`) are safely ignored during compilation.

```python
from pypost.core.json_selector_engine import JsonSelectorEngine

engine = JsonSelectorEngine(["token", "user.secret", "header:Authorization"])
```

#### `is_empty -> bool`
Returns `True` if no valid body selectors are compiled, allowing consumers to short-circuit
traversal and formatting immediately.

#### `matches(path: Sequence[str], key: str) -> bool`
Evaluates whether a dictionary key at the specified parent path matches any compiled rule.
- If `key` is present in `_bare_keys`, returns `True` immediately in $O(1)$ time.
- Otherwise, constructs the candidate path sequence (`[*path, key]`) and tests against
  `_path_selectors`.
- Includes shorthand dot fallback compatibility (e.g., matching `items.secret` against
  an `items.*.secret` rule).

```python
# Bare key match at any depth
assert engine.matches([], "token") is True
assert engine.matches(["data", "items", "0"], "token") is True

# Hierarchical dotted path match
assert engine.matches(["user"], "secret") is True
assert engine.matches(["admin"], "secret") is False
```

#### `redact_tree(node: Any, placeholder: str = "***") -> tuple[Any, int]`
Recursively redacts matching dictionary keys in arbitrary JSON structures (dictionaries and
lists). Returns a 2-tuple `(redacted_tree, masked_count)` containing the new sanitized data
structure and the total number of redacted leaf values. Non-container inputs are returned
unmodified.

```python
payload = {
    "user": {"name": "Alice", "secret": "s3cr3t"},
    "items": [{"id": 1, "token": "xyz"}],
}
redacted, count = engine.redact_tree(payload)
# count == 2
# redacted["user"]["secret"] == "***"
# redacted["items"][0]["token"] == "***"
# payload["user"]["secret"] remains "s3cr3t" (immutable)
```

#### `canonical_path(path: Sequence[str], key: str) -> str`
Static helper generating a canonical dot-notation path string (e.g. `items.*.token`).

#### `format_path_variants(path: Sequence[str], key: str) -> set[str]`
Backward-compatible static method generating all four legacy path variant representations:
bare key, `full_dot`, `shorthand_dot`, and `wildcard_dot`.

---

### 2. `CompiledPathSelector`

Located in `pypost.core.json_selector_engine`.

#### `__init__(raw: str)`
Compiles a raw path selector string. Normalizes bracket wildcards `[*]` to `.*.` and parses
into token segments.

#### `matches(candidate_tokens: Sequence[str]) -> bool`
Checks whether a sequence of tokens matches the compiled pattern length and elements. The `*`
wildcard matches any token segment.

---

### 3. MCP Redaction Integration (`SensitiveTextSanitizer`)

Located in `pypost.core.sensitive_text_sanitizer`.

```python
from pypost.core.sensitive_text_sanitizer import redact_json_response_fields

raw_body = '{"user": {"apiKey": "secret-123"}}'
sanitized = redact_json_response_fields(raw_body, hidden_fields=["user.apiKey"])
# Returns: '{"user": {"apiKey": "***"}}'
```

---

### 4. GUI Masking Integration (`ResponseMaskController`)

Located in `pypost.ui.widgets.response_mask_controller`.

`JsonMaskFormatter` uses `JsonSelectorEngine` to detect masked keys during text indentation:

```python
from pypost.ui.widgets.response_mask_controller import JsonMaskFormatter

formatter = JsonMaskFormatter(selectors=["password", "items[*].token"], indent=2)
formatted_text, spans = formatter.format(response_dict)

# formatted_text contains JSON with '***' for masked keys
# spans contains MaskedTokenSpan(raw_value=..., start=..., end=...) for click-to-reveal
```

---

## Performance Optimizations

1. **Partitioned Pre-Compilation**:
   Selectors without `.` or `[` are partitioned into `_bare_keys: set[str]`. In typical API
   responses, >80% of selectors are simple key names (`token`, `password`, `key`). These match in
   $O(1)$ time without string concatenation or tuple allocations.
2. **Zero-Allocation Non-Matches**:
   If no path selectors are defined and a key is not in `_bare_keys`, `matches()` returns `False`
   immediately without allocating path lists or string objects.
3. **Incremental Span Offset Calculation**:
   `JsonMaskFormatter` maintains `self._current_pos += len(text)` on chunk emission rather than
   summing chunk lengths on each match, reducing token span calculation complexity from
   $O(M \times N)$ to $O(1)$.

---

## Configuration

Selector patterns are configured per-request in `RequestData.hidden_response_fields: list[str]`.

Example in collection JSON persistence:
```json
{
  "name": "Get User Profile",
  "url": "https://api.example.com/v1/user",
  "method": "GET",
  "hidden_response_fields": [
    "apiKey",
    "credentials.password",
    "accounts[*].secretKey",
    "header:Authorization"
  ]
}
```

---

## Troubleshooting

- **Selector does not match nested array items**:
  Ensure array selectors specify the wildcard token, e.g. `items[*].token` or `items.*.token`.
  A selector like `items.token` uses shorthand dot fallback, but explicit wildcards are
  recommended for clarity.
- **Header selector entered in body rules**:
  Selectors prefixed with `header:` (case-insensitive) are reserved for HTTP response header
  masking and are automatically excluded from `JsonSelectorEngine`.
- **Case-sensitivity**:
  Field names are matched case-sensitively to preserve JSON specification fidelity (`apiKey`
  does not match `apikey`).
- **Non-dict/non-list payloads**:
  If the response body is raw plain text or invalid JSON, `redact_json_response_fields()` safely
  returns the original text unmodified without raising an exception.
