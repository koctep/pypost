# Unified JSON Selector Path Evaluation Engine (PYPOST-1394 / PYPOST-1388)

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

PYPOST-1388 keeps that public API frozen and replaces the hierarchical match path with a
**segment trie** (`PathSelectorTrie`) plus **mutable path breadcrumbs** during redaction and GUI
formatting, so match cost scales with path depth rather than hierarchical rule count.

---

## Architecture

The unified engine lives in `pypost/core/json_selector_engine.py`:

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
|   |   _bare_keys (set[str])  |  | PathSelectorTrie         | |
|   |   e.g. {'token', 'ssn'}  |  | exact + '*' edges        | |
|   |   $O(1)$ direct lookup   |  | terminals = mask field   | |
|   +--------------------------+  +--------------------------+ |
|                                                              |
|   - matches(path, key) -> bool                               |
|   - redact_tree(node, placeholder) -> (redacted, count)      |
|   - mutable breadcrumb (push / pop) during redact_tree       |
+------------------------------+-------------------------------+
            |                                      |
            v                                      v
+-----------------------+              +-----------------------+
| SensitiveTextSanitizer|              | ResponseMaskController|
| (MCP irreversible)    |              | JsonMaskFormatter     |
|                       |              | (same breadcrumb)     |
+-----------------------+              +-----------------------+
```

### Components

- **`PathSelectorTrie`** (PYPOST-1388):
  Prefix trie over hierarchical selector token sequences. Each node holds exact-token children
  plus an optional `*` edge. Terminals mark “mask this field.” Steady-state `matches` walks the
  trie in $O(\mathrm{depth})$ (with branching only on wildcards); it does **not** scan the full
  hierarchical rule catalog per key.
- **`CompiledPathSelector`**:
  Parses hierarchical path strings (such as `user.profile.token` or `items[*].secret`) into
  normalized token tuples (`('items', '*', 'secret')`). `_parse_tokens` remains the single
  normalization path that feeds trie inserts at compile time.
- **`JsonSelectorEngine`**:
  The central facade that normalizes and compiles raw selector strings, partitions them into
  fast bare keys and trie-indexed path selectors, determines whether an AST node matches, and
  executes immutable tree redaction with a shared mutable path breadcrumb.
- **`SensitiveTextSanitizer` Integration**:
  MCP response redaction delegates `redact_json_response_fields()` directly to
  `JsonSelectorEngine.redact_tree()`, returning a sanitized deep-copy tree and serialization.
- **`ResponseMaskController` (`JsonMaskFormatter`) Integration**:
  Interactive GUI formatting instantiates `JsonSelectorEngine` to query `engine.matches(path, key)`
  during streaming token formatting, recording character offset spans with an incremental $O(1)$
  offset counter. Descent uses the same push/pop breadcrumb pattern as engine redaction.

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

Body selection ignores a header selector by calling the same shared prefix helper
(`header_selector_name`) used by validation and header sanitization
([PYPOST-1538](https://pypost.atlassian.net/browse/PYPOST-1538)).

---

## API & Usage

### 1. `JsonSelectorEngine`

Located in `pypost.core.json_selector_engine`.

#### `__init__(selectors: Iterable[str] | None = None)`
Initializes the engine and compiles the given selector rules. Blank entries, whitespace, and
non-body selectors (e.g. `header:*`) are safely ignored during compilation. Hierarchical rules
are inserted into `PathSelectorTrie`; bare keys go into `_bare_keys`.

```python
from pypost.core.json_selector_engine import JsonSelectorEngine

engine = JsonSelectorEngine(["token", "user.secret", "header:Authorization"])
```

#### `is_empty -> bool`
Returns `True` if no valid body selectors are compiled (no bare keys and an empty trie),
allowing consumers to short-circuit traversal and formatting immediately.

#### `matches(path: Sequence[str], key: str) -> bool`
Evaluates whether a dictionary key at the specified parent path matches any compiled rule.
- If `key` is present in `_bare_keys`, returns `True` immediately in $O(1)$ time.
- Otherwise, walks `PathSelectorTrie` over `path` then `key` via `matches_path_and_key`
  (no combined candidate list allocation on the hot path).
- Includes shorthand dot fallback after a hierarchical miss. A `MaskBreadcrumb` reports
  `*` presence with `has_wildcard` (wildcard count above zero) and does not scan the
  location. A one-shot list or tuple still uses `_sequence_has_wildcard`. When presence is true, a
  second trie walk strips `*` segments (rule `items.secret` against path `items.*.secret`).

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

Internally, `_redact_node` shares one `MaskBreadcrumb`. Object keys and list stars are
pushed on descent and popped on ascent. Push of `"*"` increments a wildcard count and
pop of `"*"` decrements it, so an outer star stays in force after an inner star is
popped. Callers still receive an immutable redacted copy of the tree (inputs are never
mutated).

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

### 2. `PathSelectorTrie`

Located in `pypost.core.json_selector_engine`.

The isolated catalog in `tests/test_pypost_1545_failing_repro.py` locks insert
dedupe and size, an empty index, shorthand-only walks, bare-name rules, and the
wildcard-heavy yes-or-no, without changing mask results.

#### `insert(tokens: Sequence[str]) -> None`
Indexes one hierarchical token sequence. Duplicate terminals do not inflate `size`.

#### `size -> int`
Number of distinct terminal hierarchical paths (also emitted as `trie_size` on the
`json_selector_engine_compiled` DEBUG log).

#### `matches_path_and_key(path, key) -> bool`
Primary hot-path matcher: walk `path` tokens then `key` without allocating a combined list.

#### `matches_shorthand_path_and_key(path, key) -> bool`
Shorthand fallback: skips `*` segments in the candidate path, then walks the remainder + key.

---

### 3. `CompiledPathSelector`

Located in `pypost.core.json_selector_engine`.

#### `__init__(raw: str)`
Compiles a raw path selector string. Normalizes bracket wildcards `[*]` to `.*.` and parses
into token segments used for trie insert.

---

### 4. MCP Redaction Integration (`SensitiveTextSanitizer`)

Located in `pypost.core.sensitive_text_sanitizer`.

```python
from pypost.core.sensitive_text_sanitizer import redact_json_response_fields

raw_body = '{"user": {"apiKey": "secret-123"}}'
sanitized = redact_json_response_fields(raw_body, hidden_fields=["user.apiKey"])
# Returns: '{"user": {"apiKey": "***"}}'
```

---

### 5. GUI Masking Integration (`ResponseMaskController`)

Located in `pypost.ui.widgets.response_mask_controller`.

`JsonMaskFormatter` uses `JsonSelectorEngine` to detect masked keys during text indentation.
Like `redact_tree`, format descent shares one `MaskBreadcrumb` (`push` / `pop` for object
keys and `"*"` for array elements) instead of allocating `path + [seg]` per level. The
hierarchical miss reads `has_wildcard` from that breadcrumb rather than scanning the
location.

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
2. **Segment Trie Hierarchical Lookup (PYPOST-1388)**:
   Hierarchical rules are indexed only in `PathSelectorTrie` at compile time. Steady-state
   `matches` walks exact/`*` edges bounded by path depth, not by scanning all $R$ hierarchical
   rules. Compile DEBUG reports `trie_size` as the indexed-path count.
3. **Mutable Path Breadcrumbs (PYPOST-1388)**:
   `redact_tree` and `JsonMaskFormatter` reuse one `MaskBreadcrumb` across recursion with
   `push` / `pop`, avoiding per-level `path + [seg]` allocations. A hierarchical miss reads
   `has_wildcard` instead of scanning the location for `*`.
4. **Zero-Allocation Non-Matches**:
   If the trie is empty and a key is not in `_bare_keys`, `matches()` returns `False`
   immediately without allocating path lists or string objects.
5. **Incremental Span Offset Calculation**:
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
- **Large hierarchical catalogs feel slow**:
  Confirm rules are hierarchical (contain `.` or `[`); bare keys already match in $O(1)$.
  PYPOST-1388 trie lookup should keep non-bare misses proportional to nesting depth. Check
  DEBUG `json_selector_engine_compiled` for `trie_size`.
