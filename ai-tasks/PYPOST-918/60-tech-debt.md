# PYPOST-918: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: documented **Option A** packaging path for out-of-process
MCP of UI actions in `doc/dev/ui_actions.md` (attributable to PYPOST-918),
with no-mixing locks vs product `MCPServerImpl`, cross-links from
`mcp_integration.md` / `mcp_trust_model.md` / `agent_lifecycle.md`, and
doc-token contract tests green. Live bridge delivery was never in DoD —
explicitly deferred as future work following the documented path.

**Do not create Jira Debt tickets in this step** — list unticketed
follow-ups only (no `Jira:` browse links for new tickets).

## Shortcuts Taken

- **Docs-only Option A** instead of a deferred epic or a live bridge —
  no suitable owner epic; inventing one was heavier than documenting the
  packaging contract (architecture decision).
- **Substring / token doc locks** rather than a structured doc schema or
  runtime `MCPServerImpl` tool-list assert — same pattern as PYPOST-922;
  brittle if prose is rephrased without the locked tokens.
- **Full `make check` / full suite not re-run** in cleanup / this review.
  Validated targeted contract lock (4 passed) + prior Step 5 flake8 /
  lint on touched surfaces.
- **No production Python changes** — packaging answer lives in Markdown +
  tests only; `ui_actions.py` / `MCPServerImpl` unchanged by design.

## Code Quality Issues

- None introduced in production code (no `pypost/` edits).
- Contract test helpers are file-local (`_read`, token constants); fine
  for a single module; optional share only if more packaging-doc locks
  land (Lowest).
- Pre-existing long lines in sibling MCP doc tables / prose were not
  rewritten (out of scope).

## Missing Tests

| Scenario | Status |
| --- | --- |
| `ui_actions.md` attributes packaging to PYPOST-918 | Covered |
| Out-of-process + packaging path tokens | Covered |
| No-mix lock (`MCPServerImpl` + never mount / related) | Covered |
| Product MCP docs cross-link packaging answer | Covered |
| Explicit `@pytest.mark.timeout` / module `pytestmark` | Present (`timeout(10)`) |
| Live out-of-process agent-UI MCP bridge / e2e | Out of scope (accepted deferred) |
| Runtime assert: product tool catalog excludes UI names | Not added (architecture Option C; overkill for Lowest docs debt) |
| Every sibling `doc/dev/*` soft-wording / README index polish | Not locked — Step 8 / Low |

**No timeout-marker blockers.**

## Performance Concerns

None. Docs + disk-read unit locks only; no runtime path or bridge process.

## Follow-up Tasks

Classify for close: **Blocker** = must fix before closing this debt;
**Non-blocker** = deferred / optional.

### Blockers

None.

### Non-blockers (accepted deferred / optional)

1. **Implement live out-of-process agent-UI MCP bridge**
   - Priority: Medium when prioritized (product need); **non-blocker** for
     PYPOST-918 close — DoD is packaging path, not live delivery
   - Follow documented path: dedicated stdio / separate loopback MCP entry
     wrapping `pypost.agent.ui_actions`; **never** mount on `MCPServerImpl`;
     own bind/trust/logging separately from product MCP
   - Files (future): new agent-UI MCP entry + docs; not this debt’s surface
   - Jira: [PYPOST-952](https://pypost.atlassian.net/browse/PYPOST-952)

2. **Optional: runtime assert product MCP tool list excludes UI-action names**
   - Priority: Lowest
   - Hardens no-mix beyond Markdown tokens; needs MCP harness — deferred
     as architecture Option C
   - Files: `tests/test_mcp_server_impl.py` (or sibling) when prioritized
   - Jira: [PYPOST-953](https://pypost.atlassian.net/browse/PYPOST-953)

3. **Optional: harden packaging doc locks beyond raw substrings**
   - Priority: Lowest
   - Only if token churn becomes noisy; current 922-style locks match
     project discoverability-debt practice
   - Files: `tests/test_ui_actions_mcp_packaging_doc.py`
   - Jira: [PYPOST-954](https://pypost.atlassian.net/browse/PYPOST-954)

4. **Step 8 polish: README / remaining soft-wording discoverability**
   - Priority: Low — **addressed in Step 8** (`doc/dev/README.md` TOC +
     soft-wording tightening in MCP/lifecycle docs). Kept as historical
     note; no further action.
   - Jira: **not ticketed this run**

## Deviations from Architecture

None material. Shipped Option A (documented path) + Option B (doc-token
locks) as planned. Live bridge (architecture “future” subgraph) remains
unshipped by design — recorded above as non-blocker deferred work.

## Blocker Verdict

**SAFE TO CLOSE** — no blockers relative to DoD. Live bridge and optional
hardening items above are **non-blocking**. No Jira Debt issues created
in this step.
