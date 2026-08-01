# PYPOST-1015: Technical Debt Analysis

**Verdict:** Meaningful docs-maintenance debt exists (no application-code debt).
None of it blocks shipping the User Guide. SAFE TO CLOSE for this story's DoD.

Scope reviewed: `doc/user/*`, `doc/README.md`, root `README.md` Documentation
section, and `ai-tasks/PYPOST-1015/*`. No application packages changed.

## Shortcuts Taken

- **No screenshots or layout diagrams** — Interface, Getting Started, Settings,
  and MCP pages describe UI in text only. Faster to ship; harder for first-time
  visual learners to orient.
- **No docs lint / link-check CI** — Requirements and architecture explicitly
  declined a docs-contract test. Step 5 used a manual Markdown scan (line
  length, trailing WS, ATX headers). Nothing in `make check` or GitHub Actions
  guards `doc/user/` after merge.
- **Thin orientation / reference pages by design** — `hotkeys.md` (~47 lines)
  defers to in-app **Help → Hotkeys**; `interface.md` (~50 lines) is a layout
  map without a visual; `templating.md` / `history-and-curl.md` are compact
  how-tos. Collections/environments remain the deepest pages (~136–140 lines).
- **Accuracy is human-gated** — Step 4 corrected labels/defaults against
  current UI, but there is no process or test that fails when a menu string,
  default port, or hotkey changes in code.
- **Root README list style left alone** — Documentation section keeps project
  `*` bullets while `doc/user/` uses `-` (documented in `40-code-cleanup.md`).

## Code Quality Issues

- **No application code debt** — this story did not touch `pypost/`.
- **Hotkeys duplication risk** — the guide tables a common subset that can
  drift from the live Help dialog and from shortcuts mentioned on other pages
  (`Ctrl+F`, history copy).
- **Settings depth is uneven** — retries/alerts and encryption are summarized;
  readers still need the dialog for full control names and migration flows.
- **Interface page is orientation-only** — no annotated screenshot of menu /
  env bar / sidebar / editor / response pane; relies on prose lists.
- **Related examples link is a soft dependency** — guide index and workflows
  point at `examples/README.md`, which was out of scope for this ticket; if
  fixtures lag, the "start from a shipped example" path weakens.

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Product / pytest coverage for this story | N/A — docs-only |
| Explicit pytest timeout markers | N/A — no new/changed tests |
| Markdown style lint (`doc/user/`) in CI | Missing (TD-1) |
| Relative link checker for guide + docs index | Missing (TD-2) |
| Docs-contract / TOC completeness check | Declined in requirements; still a gap (TD-1/TD-2) |
| Screenshot freshness checks | Missing (TD-3) |
| UI-label drift vs documented strings | Missing (TD-4) |

Internal relative links under `doc/user/` and `doc/README.md` were spot-checked
during this review (55 targets, 0 broken). That check is not automated.

## Performance Concerns

None. Static Markdown has no runtime cost. Large response truncation (~50 MB)
documented in `requests.md` is product behavior, not a docs performance issue.

## Deviations from Architecture

None material. Delivered IA matches `20-architecture.md` (twelve-topic TOC,
hub-and-spoke entry points, link-out to MCP/Prometheus, Operator metrics kept
in `workflows.md`, no Diátaxis folder redesign).

## Follow-up Tasks

Concrete items for the orchestrator to ticket later via `jira-create-issue`.
**No Jira browse links yet.**

| ID | Priority | Item | Notes |
| -- | -------- | ---- | ----- |
| TD-1 | Medium | Add a Makefile/`make check` (or CI) Markdown lint for `doc/user/` and `doc/README.md` (line length ≤100, trailing WS, ATX headers, list consistency) | Closes the Step 5 "manual scan only" gap; prevents format regressions. Jira: [PYPOST-1020](https://pypost.atlassian.net/browse/PYPOST-1020) |
| TD-2 | Medium | Add a relative link checker for User Guide + docs index (+ optional root README Documentation links) | Prevents broken TOC/cross-links after renames; complements TD-1. Jira: [PYPOST-1021](https://pypost.atlassian.net/browse/PYPOST-1021) |
| TD-3 | Low | Add annotated screenshots (or a simple layout diagram) to `interface.md` and Getting Started first-run | Biggest UX gap for new users; keep assets small and alt-texted per markdown guidelines. Jira: [PYPOST-1022](https://pypost.atlassian.net/browse/PYPOST-1022) |
| TD-4 | Medium | Define a docs accuracy-drift checklist when UI labels, defaults, or hotkeys change (owner + when to re-read `doc/user/`) | Highest ongoing risk for a docs-only ship with no contract tests. Jira: [PYPOST-1023](https://pypost.atlassian.net/browse/PYPOST-1023) |
| TD-5 | Low | Expand thin reference pages where prose alone is ambiguous (Settings encryption migration steps; Hotkeys vs in-app-only shortcuts) | Only if support questions show confusion; avoid duplicating the full Help dialog. Jira: [PYPOST-1024](https://pypost.atlassian.net/browse/PYPOST-1024) |

### Accepted / out of scope (do not ticket from this story)

- Absorbing full MCP Integration / Prometheus Monitoring into the User Guide.
- Developer docs under `doc/dev/`.
- Example fixture authorship (owned elsewhere; guide already links).
- Application feature work or in-app help browser.

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | Docs process shortcuts only; none block ship |
| Missing tests with timeout markers | **N/A** — no Python tests in scope |
| Deviations from architecture | None |
| Acceptance gaps vs DoD | **None** — index, twelve topics, docs index + README wiring present |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-1015; follow-ups are maintenance improvements.
