# PYPOST-838: Technical Debt Analysis

## Shortcuts Taken

- Golden flow relies on a blank restored tab (fresh `data_dir`) instead of
  clicking “new request”; open/create is satisfied without exercising the
  plus-tab control.
- Response status/body still have no dedicated `objectName`s; wait + assert
  use snapshot text under `RESPONSE_PANEL` (architecture fallback — no catalog
  growth).
- Assertions match `FIXTURE_BODY_IN_SNAPSHOT` (compact JSON from
  `sanitize_text`), not the pretty-printed `QTextEdit` form — two constants
  encode that seam.
- HTTP is mocked only for the happy-path 200; error statuses, retries, and
  live network are out of scope by design.
- Exactly one golden scenario (AC bar); no matrix of methods/bodies/dialogs.

## Code Quality Issues

- Test-local snapshot walkers (`_walk_values`, `_subtree_by_name`,
  `_response_panel_excerpt`) duplicate patterns that could live next to
  `ui_snapshot` helpers if more goldens share them.
- `UiWaitTimeoutError` rewrap on settle failure is verbose but intentional for
  FR10 (`step` + clipped `response_excerpt`).
- Coupling to sanitize/re-dump behavior: if snapshot JSON formatting changes,
  the golden body assert must be updated even when the widget still shows the
  same pretty text.

## Missing Tests

- No dedicated failure-path test that forces wait timeout and checks
  `response_excerpt` / `step` diagnostics (happy path only).
- No golden for non-JSON / plain-text response bodies.
- No coverage of plus-tab create when restore does not open a blank tab.
- No product-dialog settle after Send (settings / confirm) — left to broader
  packaging or a later flow.

## Performance Concerns

- Post-Send settle uses `wait_for_snapshot` (full-tree poll). Acceptable for one
  e2e proof; same cost profile as PYPOST-837 notes for long timeouts + heavy
  trees. Prefer widget/text waits only after status/body get stable ids.

## Follow-up Tasks

Jira: [PYPOST-853](https://pypost.atlassian.net/browse/PYPOST-853)

| ID | Priority | Summary | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Optional `pypost_response_status` / `pypost_response_body` ids | [PYPOST-920](https://pypost.atlassian.net/browse/PYPOST-920) |
| TD-2 | Low | Share panel subtree / value-walk helpers | Delivered in [PYPOST-853](https://pypost.atlassian.net/browse/PYPOST-853) |
| TD-3 | Medium | Failure-path golden (forced settle timeout) | Delivered in [PYPOST-853](https://pypost.atlassian.net/browse/PYPOST-853) |
| TD-4 | Low | Plus-tab create path when blank restore changes | [PYPOST-921](https://pypost.atlassian.net/browse/PYPOST-921) |
| TD-5 | Medium | Broader agent-e2e packaging / `make` entry | [PYPOST-922](https://pypost.atlassian.net/browse/PYPOST-922) |

No blockers relative to acceptance criteria. Composition proof (lifecycle +
identity + actions + wait + snapshot + mocked HTTP → response UI) is complete;
debt is follow-on coverage and ergonomics, not missing DoD.
