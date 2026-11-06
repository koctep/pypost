# PYPOST-1339: Technical Debt Analysis

Scope: trustworthy surviving-template-marker checks for MCP example collections —

- `tests/test_github_mcp_collection.py` — full-render body surface uses
  `_render(request.body, variables)`; nested-object-final twin
  `test_github_mcp_nested_object_final_body_field_does_not_false_positive_markers`
- `tests/test_gitlab_mcp_collection.py` — same body-surface correction on
  `test_gitlab_mcp_full_render_leaves_no_template_markers`
- `examples/collections/github_mcp.json` — `github_dispatch_workflow` emits
  `ref` then `inputs` (nested-object-final)
- `doc/dev/github_mcp_collection.md` — field-order note updated for PYPOST-1339

No production `pypost/` runtime change. Closes parent
[PYPOST-1334](https://pypost.atlassian.net/browse/PYPOST-1334) TD-1.

**No item below is a BLOCKER.** Both MCP collection modules declare
`pytestmark = pytest.mark.timeout(30)`, covering the twin and updated
full-render tests. The do-testing explicit-timeout rule is met.

Phase D / tech-debt-jira-sync creates or closes Jira issues; this step only
records candidates. Do **not** create issues here.

## Summary Table

| ID | Priority | Item | Follow-up |
| --- | --- | --- | --- |
| TD-1 | — | Parent nested-object `}}` false positive (scan `json.dumps(parsed)`) | **resolved here** — close/verify [PYPOST-1334](https://pypost.atlassian.net/browse/PYPOST-1334) TD-1 / this ticket |
| TD-2 | Low | Marker-scan loop duplicated (GitHub full-render, twin, GitLab) | no new — existing [PYPOST-1340](https://pypost.atlassian.net/browse/PYPOST-1340) (shared MCP collection helpers) |
| TD-3 | Lowest | Substring `_TEMPLATE_MARKERS` can still false-positive on string **values** containing `{{` / `}}` / `{%` / `%}` | no (accepted residual; unchanged by design) |
| TD-4 | Low | No mutation twin that injects a leftover body marker and asserts failure | [PYPOST-1507](https://pypost.atlassian.net/browse/PYPOST-1507) |
| TD-5 | Lowest | Twin + full-render each rebuild the surface list; no in-module private helper | no (local polish; fold into PYPOST-1340 or leave) |
| TD-6 | Medium | `make lint` still does not flake8 `tests/` | no new — existing [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303) |
| TD-7 | — | GitLab has no nested-object-final twin of its own | no (out of scope; GitHub twin + shared scan rule sufficient) |

## Shortcuts Taken

- **Raw `_render(request.body, …)` instead of `ResolvedRequestFields.body`.**
  `_prepare` still discards the resolved fields from
  `HTTPClient._prepare_request_kwargs`. Calling `_render` again matches
  `_render_body_json` and avoids widening `_prepare`. Wire path and marker
  path use the same template + variables; double render is negligible offline.
  Accepted architecture choice; not worth a ticket.

- **Local duplication over shared helpers.** GitHub and GitLab each append
  `_render(...)` in their full-render loops; the twin mirrors the same surface
  list. Extracting to `tests/helpers/` was explicitly deferred to
  [PYPOST-1340](https://pypost.atlassian.net/browse/PYPOST-1340) (parent TD-2).
  See TD-2 / TD-5.

- **Optional field-order restore landed.** Dispatch body now emits `ref` then
  `inputs` so the suite itself carries the nested-object-final shape the twin
  asserts. Natural docs order; API semantics unchanged (RFC 8259 unordered
  objects). Clarity cleanup, not a shortcut.

- **Residual string-value substring risk left alone.** Architecture explicitly
  accepted that marker substrings in legitimate JSON string values can still
  trip the check. This ticket only removed the structural nested-object false
  positive. See TD-3.

## Code Quality Issues

- **TD-2 (Low) — duplicated marker-scan across provider suites.**
  The corrected body line and assert loop exist in both
  `test_*_mcp_full_render_leaves_no_template_markers` implementations (and the
  GitHub twin). A future regression to `json.dumps(parsed)` must be fixed in
  two places until PYPOST-1340 centralizes the contract. Do not re-file; attach
  any marker-surface helper work to that ticket.

- **TD-5 (Lowest) — in-module surface-list duplication.**
  Twin and GitHub full-render rebuild
  `[url, *headers, *params, _render(body)]` independently so the twin documents
  the contract without a shared private helper. Optional one-liner helper inside
  `tests/test_github_mcp_collection.py` only; not a Debt issue on its own.

- **No unexplained architecture deviation.** Body surface is raw rendered text;
  twin asserts `list(body_obj)[-1] == "inputs"`; GitLab gets the latent fix
  without its own nested tool; production HTTP client unchanged; timeouts
  preserved.

- **Hardcoded values (intentional):** `_TEMPLATE_MARKERS`, module timeout 30s,
  OFFLINE_ENV sample inputs. Documented test contracts; not debt.

## Missing Tests

- **Timeouts:** not missing.

  | Module | Marker |
  | --- | --- |
  | `tests/test_github_mcp_collection.py` | `pytestmark = pytest.mark.timeout(30)` |
  | `tests/test_gitlab_mcp_collection.py` | `pytestmark = pytest.mark.timeout(30)` |

- **DoD paths covered:** raw-body scan on GitHub + GitLab full/minimal renders;
  nested-object-final twin on `github_dispatch_workflow`; fixture order restored.

- **TD-4 (Low) — no positive mutation for leftover body markers.**
  Sibling checkers in the GitHub module often pair a contract with a synthetic
  mutation twin. The marker check relies on continuing to scan
  `_TEMPLATE_MARKERS` without a test that deliberately leaves `{{` (or similar)
  in a rendered body and expects failure. Regression risk is low (assert loop
  still present) but a small mutation would lock DoD item 3. Optional follow-up.

- **TD-7 — no GitLab nested-object twin.** Requirements asked for one twin;
  GitHub dispatch is the reproducing fixture. No follow-up.

## Performance Concerns

None. Extra `_render` per full-render iteration is offline template work only;
negligible vs collection load and `_prepare`.

## Follow-up Tasks

Specific tasks for Phase D / tech-debt Jira sync (do **not** create issues in
Step 7):

1. **TD-1 — Close/verify parent nested-object marker false positive**  
   Confirm [PYPOST-1334](https://pypost.atlassian.net/browse/PYPOST-1334) TD-1
   / this issue ([PYPOST-1339](https://pypost.atlassian.net/browse/PYPOST-1339))
   is marked done once the gate accepts Steps 7–8 / commit. Do not re-file TD-1.

2. **TD-2 — Shared MCP collection marker-surface helper** (Low)  
   When extracting shared helpers, include the raw-body marker surface so GitHub
   / GitLab / future providers cannot diverge back to `json.dumps(parsed)`.  
   Jira: existing [PYPOST-1340](https://pypost.atlassian.net/browse/PYPOST-1340)

3. **TD-4 — Mutation twin for leftover body template markers** (Low)  
   Add a synthetic case (GitHub module is enough) that injects an unrendered
   marker into a body template (or rendered string under test) and asserts the
   surviving-marker check fails. Keeps DoD item 3 regression-proof.  
   Jira: [PYPOST-1507](https://pypost.atlassian.net/browse/PYPOST-1507)

4. **TD-6 — Existing lint debt** (Medium)  
   [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303) — `make lint`
   flake8 for `tests/`. Do not duplicate.

**Accepted / no new ticket:** TD-3 (string-value substring residual), TD-5
(local surface-list duplication), TD-7 (GitLab twin N/A).

## User documentation

Optional clarity already applied in `doc/dev/github_mcp_collection.md` (field
order + PYPOST-1339 pointer). No end-user product docs. Further polish, if any,
belongs in Step 8.

## Independent Closure Review

Left for the gate owner / review subagent. This execution leaves STEP 7 `[/]`
and does not create Jira issues.
