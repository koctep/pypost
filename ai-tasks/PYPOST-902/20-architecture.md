# PYPOST-902: Optional method+URL compound map keys

## Research

### Jira / parent debt

- Issue: [PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902) — optional
  method+URL compound map keys on the Mapping router.
- Parent: [PYPOST-868](https://pypost.atlassian.net/browse/PYPOST-868) shipped
  exact-URL-only router; debt note in `ai-tasks/PYPOST-868/60-tech-debt.md`.
- Acceptance: extend match rules (e.g. `GET https://…` keys) and document
  precedence vs bare URL keys.

### Existing infrastructure

| Layer | Location | Status |
| --- | --- | --- |
| URL router | `pypost/fixtures/agent_e2e_http.py` — `url_router_side_effect` | v1 exact URL |
| Unit proofs | `tests/test_agent_e2e_http.py` — map hit, miss, restore | Green |
| GUI multi-URL | `tests/test_agent_e2e_http_mapping_multi_url.py` (901) | Green; distinct URLs |
| Docs | `doc/dev/agent_e2e_http.md` — match rules § URL router | Lists compound keys as “not v1” |

### Match algorithm (v2 additive)

For each `send_request` call:

1. Extract `method` and `url` from `request_data` (existing helper).
2. Build compound key `f"{method} {url}"`.
3. If compound key ∈ map → return that canned result.
4. Else if `url` ∈ map → return bare URL entry (v1 backward compat).
5. Else → `AssertionError` with `url=` and sorted known keys (unchanged message shape).

**Precedence:** When map contains both `"GET https://host/path"` and
`"https://host/path"`, a GET request matches the compound entry first. A POST
to the same URL matches only the bare entry if no `POST …` compound key exists.

No new logging events — reuse `agent_e2e_http_stub_installed name=url_router`.

## Implementation Plan

1. **Failing repro (Step 3)** — add
   `test_stub_agent_e2e_http_url_router_method_url_compound_keys` in
   `tests/test_agent_e2e_http.py`: map keyed by `GET {url}` / `POST {url}` for
   same URL; assert distinct canned bodies. Fails on v1 (AssertionError / wrong
   route).
2. **Development (Step 4)** — extend `_resolve_url_router_response` (new helper)
   or inline lookup in `url_router_side_effect`; update docstring on router +
   `stub_agent_e2e_http` Mapping overload.
3. **Additional unit tests (Step 4)** — bare URL fallback unchanged;
   compound-over-bare precedence; miss message still lists keys.
4. **Docs (Step 8)** — update `doc/dev/agent_e2e_http.md` match rules (remove
   “not in v1” for compound keys; add precedence bullets + example map).
5. **Cleanup / observability (Steps 5–6)** — no new log events; flake8 on touched
   files.

### Failing Repro (Step 3)

```python
def test_stub_agent_e2e_http_url_router_method_url_compound_keys() -> None:
    shared = "https://example.test/shared"
    responses = {
        f"GET {shared}": make_canned_http_result(url=shared, body='{"via":"get"}'),
        f"POST {shared}": make_canned_http_result(url=shared, body='{"via":"post"}'),
    }
    # GET and POST to same URL → distinct canned results
```

Expected failure on v1: `AssertionError` — compound keys not recognized.

## Files Touched

| File | Change |
| --- | --- |
| `pypost/fixtures/agent_e2e_http.py` | Compound + bare lookup in router |
| `tests/test_agent_e2e_http.py` | Red test + precedence / compat tests |
| `doc/dev/agent_e2e_http.md` | Match rules + example |

## Out of Scope

- Glob/prefix, ordered queues, GUI compound-key scenario.
- Case-folding HTTP methods.
