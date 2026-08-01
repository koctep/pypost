# PYPOST-959: HTTP method case normalization in URL router

## Research

### Origin

- Jira: [PYPOST-959](https://pypost.atlassian.net/browse/PYPOST-959) — optional
  HTTP method case normalization in compound-key URL router.
- Parent: [PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902)
  `60-tech-debt.md` follow-up row.
- Router: `pypost/fixtures/agent_e2e_http.py` — `_resolve_url_router_response`.

### Existing infrastructure

| Layer | Location | Status |
| --- | --- | --- |
| Compound lookup | `_resolve_url_router_response` | Method as-is from request |
| Unit proofs | `tests/test_agent_e2e_http.py` — compound keys (902) | Green |
| Docs | `doc/dev/agent_e2e_http.md` — match rules | No normalization note |

**Missing:** Request method uppercasing before compound key build.

### Match algorithm (additive)

For compound lookup only:

1. Extract `method` and `url` from `request_data` (unchanged).
2. Build compound key `f"{method.upper()} {url}"`.
3. If compound key ∈ map → return canned result.
4. Else bare URL fallback (unchanged).
5. Else miss (unchanged).

Bare URL keys and error message shape unchanged. Map authors continue using
uppercase methods in compound keys (`GET`, `POST`, …).

## Implementation Plan

1. **Failing repro (Step 3)** — add
   `test_stub_agent_e2e_http_url_router_compound_key_mixed_case_method`:
   map keyed `GET {url}`; request `method="get"`; assert canned hit. Fails
   on current code (`AssertionError` or miss).
2. **Development (Step 4)** — `method.upper()` in `_resolve_url_router_response`;
   update docstrings on helper and `url_router_side_effect`.
3. **Docs (Step 8)** — add normalization bullet under match rules in
   `doc/dev/agent_e2e_http.md`.
4. **Cleanup / observability (Steps 5–6)** — no new log events; lint touched files.

### Failing Repro (Step 3)

```python
def test_stub_agent_e2e_http_url_router_compound_key_mixed_case_method() -> None:
    shared = "https://example.test/mixed-case"
    result = make_canned_http_result(url=shared, body='{"via": "get"}')
    responses = {f"GET {shared}": result}
    req = RequestData(method="get", url=shared)
    # expect hit; v1 raises AssertionError (unknown url)
```

## Files Touched

| File | Change |
| --- | --- |
| `pypost/fixtures/agent_e2e_http.py` | Uppercase method in compound lookup |
| `tests/test_agent_e2e_http.py` | Mixed-case method unit proof |
| `doc/dev/agent_e2e_http.md` | Normalization note in match rules |

## Out of Scope

- Map-key case folding, bare URL case changes, GUI mixed-case scenario.
