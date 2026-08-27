# PYPOST-1208: Developer Documentation (Step 8)

ATTACH-3 under epic
[PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991). Step 4 already
landed the proven-vs-manual table in `doc/dev/agent_ui_actions_mcp.md`. This
step **confirmed** that table against `tests/test_agent_ui_attach.py`,
refined proof-scope notes so docs do not overclaim, and added discoverability
cross-links. No new attach capability.

## Decision

**Confirm + refine existing ATTACH-3 verification docs** — no new feature
page; document only what tests prove versus manual gaps.

| Surface | Step 8 action |
| --- | --- |
| `doc/dev/agent_ui_actions_mcp.md` | Refined Proven vs manual (proof scope notes; discoverability links) |
| `doc/dev/README.md` | TOC entry points at Proven vs manual (PYPOST-1208) |
| `doc/dev/testing.md` | Coverage table row + § Agent-UI attach verification |
| `doc/dev/ui_actions.md` | Packaging + Related pointers to ATTACH-3 matrix |
| `doc/dev/agent_lifecycle.md` | Full-matrix pointer → Proven vs manual anchor |
| New `doc/dev/<feature>.md` | **Not created** — primary page already owns the matrix |
| `doc/user/` | Out of scope |

## Docs ↔ tests agreement

| Scenario | Doc claim | Test / note |
| --- | --- | --- |
| CLI `--attach` | Automated | `test_cli_accepts_attach_mode` |
| No silent spawn / unbound fail | Automated | attach-mode + unbound tests |
| Host+client `ui_click` / fill / select / send_key | Automated | four host+client catalog tests |
| Detach / host exit / sidecar exit | Automated | lifecycle trio; host exit = `stop()` |
| Endpoint override | Automated | env/default + CLI help (not full serve) |
| UI tools off product MCP | Automated | `test_list_tools_excludes_agent_ui_action_names` |
| Protocol-version reject | Manual | PYPOST-1218 |
| Concurrent / stale-socket | Manual | accepted residual |

Eleven attach tests in `tests/test_agent_ui_attach.py` (`pytestmark` timeout
30). Manual rows stay explicit with check / pass criteria.

## Skill sections (template mapping)

| td-70 section | Where |
| --- | --- |
| Overview | Existing Overview (spawn vs attach) — unchanged |
| Architecture | Existing Architecture — unchanged |
| Usage | Attach path + Proven vs manual |
| Configuration | Existing Configuration — unchanged |
| Troubleshooting | Existing Troubleshooting — unchanged |

## What Step 8 changed

- Clarified host-exit and endpoint automated proof **scope** (no overclaim).
- Cross-linked README / testing / ui_actions / agent_lifecycle to the matrix.
- Recorded this gate artifact.

No product code, no new capability, no inventing CI coverage for manual rows.

## Completion criteria (this step)

- [x] Proven vs manual agrees with `tests/test_agent_ui_attach.py`
- [x] ATTACH-3 verification discoverable from README / testing / ui_actions
- [x] Decision recorded in this artifact + roadmap Step 8 sub-items
- [ ] Gate: leave Step 8 `[/]` until review / acceptance
