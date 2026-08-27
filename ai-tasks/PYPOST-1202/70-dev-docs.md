# PYPOST-1202: Developer Documentation (Step 8)

DECOMPOSE / planning task — children under
[PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991) already exist.
This step records the `doc/dev` decision for the decompose story only.

## Decision

**Minimal product-doc change only** — a ticket pointer, not attach docs.

| Change | Rationale |
| --- | --- |
| Update `doc/dev/agent_ui_actions_mcp.md` Limitations | Existing “attach unsupported” sentence now points maintainers at the ticketed children |
| Do **not** document attach path, trust boundary, or lifecycle | Owned by ATTACH-1 ([PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206)) |
| Do **not** document attach capability or tests | Owned by [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207) / [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208) |
| No new `doc/dev/<feature>.md` | No product feature shipped on PYPOST-1202 |
| No `doc/user/` | Out of scope for this decompose story |

## What was updated

In `doc/dev/agent_ui_actions_mcp.md` § Limitations (v1), the attach-unsupported
bullet now references epic PYPOST-991 and Stories PYPOST-1206 / 1207 / 1208,
and states that attach contract prose belongs to PYPOST-1206.

## Skill sections (template mapping)

For this ticket type, the td-70 template (Overview / Architecture / Usage /
Configuration / Troubleshooting) is **satisfied by the existing sidecar doc**
plus the Limitations pointer. Full attach sections land when ATTACH-1 runs
its own Step 8.

## Completion criteria (this step)

- [x] `doc/dev` touched only as needed (pointer; no ATTACH-1 prose)
- [x] Decision recorded in roadmap Step 8 notes and this artifact
- [ ] Gate: leave Step 8 `[/]` until review / acceptance
