# PYPOST-902: Dev Docs (Step 8)

## Updated

| File | Change |
| --- | --- |
| `doc/dev/agent_e2e_http.md` | Match rules: compound keys, precedence, same-URL example; troubleshooting row |

## Not changed

- `doc/dev/agent_e2e.md` — no new harness module; compound keys are API doc on existing router
- `doc/dev/testing.md` — no new test tier or marker

## Author guidance summary

- Prefer bare URL keys when methods differ by URL (868 / 901 pattern).
- Use `f"{method} {url}"` keys when two methods share one resolved URL.
- Compound match is tried before bare URL fallback.

## Verification

Docs align with `url_router_side_effect` / `_resolve_url_router_response` in
`pypost/fixtures/agent_e2e_http.py` and unit tests in
`tests/test_agent_e2e_http.py`.
