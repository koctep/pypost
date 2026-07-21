# PYPOST-887: Response body shown twice for PUT with nested/malformed JSON

## Goals

API clients must show each HTTP response body **exactly once**. When PyPost
prints or displays the same response twice, users cannot trust what the server
actually returned. That breaks debugging: status and body look duplicated,
payload size looks wrong, and copy/paste or comparison against expected
output becomes unreliable.

This bug was reported for a PUT request whose request body used an extra outer
brace wrap (malformed / nested JSON-like text). The business goal is to restore
trustworthy, single presentation of the response whenever a request is sent —
starting from the reported case, and clarifying whether the defect is limited
to that case or affects response display more broadly.

## User Stories

- As an API tester, I want each response body shown once after I send a
  request, so that I can trust what the server returned and debug accurately.
- As an API tester, I want correct single display even when my request body is
  malformed or oddly nested JSON, so that a body typo does not corrupt how
  the response is presented.
- As an API tester, I want the same single-display guarantee for the HTTP
  methods I use in practice (at least the reported PUT case), so that I am
  not misled only on certain verbs.

## Definition of Done

- Reproducing the reported scenario (PUT, URL as in the report, raw body of
  the form `{ { "data": { } } }`) shows the HTTP response body **once** in
  the user-visible output — not twice.
- Valid request bodies continue to show the response body once (no
  regression in the normal happy path).
- Scope of the fix matches the agreed breadth (see Q&A): either the
  reported PUT + malformed-body case only, or any other methods/bodies that
  show the same double presentation for a single send.
- Before a fix is applied, the double-display defect must be demonstrable
  via an automated verification that fails on the buggy behavior and passes
  once the defect is resolved.
- User-facing behavior for sending requests and viewing responses remains
  otherwise unchanged (no new product features required by this bug).

## Task Description

### Problem

When a user sends a PUT request with a malformed / extra-wrapped JSON-like
body, the HTTP response body appears twice in PyPost's output instead of
once.

**Steps to reproduce (from report):**

1. Create a request: Method PUT, URL `https://portal.velvetel.net/v2/user_auth`,
   Body (raw JSON-like): `{ { "data": { } } }`.
2. Send the request.
3. Observe the response output.

**Expected:** response body shown once.

**Actual:** response body printed twice.

### Scope (in)

- Correct single presentation of the response body for the reported case.
- Confirm whether double presentation is specific to malformed bodies, PUT,
  or response presentation in general — and fix to the agreed scope.
- Automated verification that the double-display defect is reproducible
  before the fix lands, and that it no longer occurs afterward.

### Scope (out)

- Changing how malformed request bodies are validated, rejected, or edited
  (unless required solely to stop double display — preference is display
  correctness without new body-validation product rules).
- Redesigning the response viewer or request editor UX beyond stopping
  duplicate presentation.
- Guaranteeing success or specific content from the third-party URL in the
  report; the URL is a reproduction context, not a product dependency.

### Constraints and assumptions

- **Programming language:** Python (PySide6), matching the existing product.
- "Printed twice" means the same response content appears duplicated in
  whatever surface the user uses to read the result after Send (UI and/or
  equivalent output the product shows for that send).
- The report's body shape (extra outer braces) is the known trigger; other
  body shapes and methods may or may not be affected — that must be
  clarified during later investigation without expanding product scope
  beyond trustworthy single display.
- Process constraint: after architecture is agreed, an automated check that
  demonstrates the double-display defect is required before the corrective
  change is accepted.

### Main entities (business)

- **Request** — method, URL, and body the user prepares and sends.
- **Response** — status and body returned for a single send; must be
  presented once per send.
- **Response presentation** — the user-visible depiction of that response
  after Send.

## Q&A

- **Q:** Why fix this if the request body is malformed anyway?
  **A:** Malformed input must not undermine trust in what the *server*
  returned. Users often iterate on body shape while debugging; duplicate
  response text makes that work unsafe and confusing.

- **Q:** Is the goal only the reported PUT + malformed body case?
  **A:** Minimum acceptance is fixing the reported reproduction. If the
  same double presentation appears for other methods or valid bodies, the
  business expectation is still "show once per send" for those cases too —
  confirm breadth during architecture / investigation (open for review).

- **Q:** Does "printed twice" include history, logs, MCP tool output, or
  only the main response pane?
  **A:** Open — confirm with reporter/product. Default assumption for this
  bug: the primary post-Send response view the user watches when following
  the reproduction steps. Broader surfaces only if they show the same
  duplication for that send.

- **Q:** Must the third-party URL remain part of automated verification?
  **A:** Open for architecture. The business need is reliable proof of
  single vs double presentation; the product goal does not require that
  host to stay reachable or return a particular payload.

- **Q:** Any new user-facing feature required?
  **A:** No — restore correct single display and guard it with automated
  verification.
