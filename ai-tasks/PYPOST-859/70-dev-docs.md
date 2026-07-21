# PYPOST-859: Developer Documentation

## Overview

Step 7 updates developer docs for the deterministic HTTP fixture layer
(shared canned catalog + stub at `HTTPClient.send_request`).

## Files Created / Updated

| File | Change |
| --- | --- |
| `doc/dev/agent_e2e_http.md` | **New** — overview, architecture, API, how to add canned, troubleshooting |
| `doc/dev/agent_e2e_env.md` | Status → Delivered; prefer shared HTTP; Related link |
| `doc/dev/agent_e2e.md` | Architecture row, fixtures table, tools map, harness module, Related |
| `doc/dev/agent_golden_e2e.md` | Migrated to `stub_agent_e2e_http(CANNED_GOLDEN_OK)` |
| `doc/dev/agent_e2e_seed.md` | Cross-link to HTTP doc |
| `doc/dev/logging.md` | `agent_e2e_http_stub_installed` catalog + Related |
| `doc/dev/README.md` | TOC entry for HTTP fixture layer |

## Sections Covered

- Overview / Architecture / Usage / Configuration / Troubleshooting on
  `agent_e2e_http.md`
- “How to add a new canned response” checklist in that page
- Golden + env contract pages aligned with shared layer (no one-off patch
  as primary path)

## Notes

User-facing `doc/user/` was out of scope (test harness / env pack only).
