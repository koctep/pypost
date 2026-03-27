# Requirements: PYPOST-422

## References

- **Jira:** PYPOST-422
- **Related:** [PYPOST-402](https://pypost.atlassian.net/browse/PYPOST-402) (source feature),
  tech debt **PYPOST-402-TD5** (misleading metric name)

## Problem statement

The Prometheus counter currently exposed as `email_notification_failures_total` is
incremented when **all retries for an HTTP request are exhausted**, not only for
email-specific notification flows. The name suggests a narrower, domain-specific
meaning than what the implementation records. That mismatch confuses anyone building
dashboards, alerts, or runbooks and undermines trust in metrics naming across the
product.

The business need is **clear, honest labeling** of what this counter measures so
operators and integrators can interpret and alert on it correctly.

## Scope

### In scope

- Defining what this counter must communicate to humans (name and/or supporting
  description) so it is not read as “email-only” unless that is truly the case.
- Ensuring consistency across **exported metrics**, **automated tests** that assert
  metric names, and **developer-facing documentation** that references this series.
- Acknowledging impact on consumers who already graph or alert on the old name
  (coordination or migration expectations at the business level).
- Communicating the change to owners of dashboards, alert rules, and saved queries
  (internal platform teams and similar) so they can plan updates alongside the
  release.

### Out of scope

- Changing **when** the counter increments (retry or error semantics), unless a
  separate task explicitly requires it.
- Broader redesign of the metrics subsystem, unrelated counters, or alert routing
  logic beyond what is needed to align naming and docs with behavior.
- Product UI copy outside metrics and technical documentation tied to this series.

## Functional requirements

1. **FR-1 (Truthful naming):** The primary Prometheus series name (or an approved
   alias strategy documented for operators) must not imply that increments are
   limited to email notification failures if the implementation counts a broader
   class of events (e.g., generic request retry exhaustion).

2. **FR-2 (Discoverability):** Release notes or developer documentation for this
   change must state how monitoring consumers should find and query the metric after
   the update, including any rename or deprecation of the previous name.

3. **FR-3 (Label semantics unchanged unless specified elsewhere):** The meaning of
   existing labels (e.g., endpoint) must remain consistent with current behavior;
   this task addresses naming clarity, not new dimensions.

4. **FR-4 (Traceability):** Work must remain traceable to PYPOST-422 and the
   original PYPOST-402 TD-5 finding so audits and sprint reports stay aligned.

## Non-functional requirements

1. **NFR-1 (Consistency):** Naming must follow existing conventions for counters in
   the same codebase (suffixes, label style, English descriptions).

2. **NFR-2 (Operational safety):** Any breaking change to the exported metric name
   must be called out so teams can update dashboards and alerts; avoid silent
   divergence between docs and runtime.

3. **NFR-3 (Testability):** Automated checks must validate the exposed series name
   (or documented contract) so regressions are caught in CI.

4. **NFR-4 (Maintainability):** Code that registers or increments this counter
   should remain readable and aligned with the public metric name (no misleading
   internal identifiers where avoidable).

## Acceptance criteria

- **AC-1:** Exported Prometheus counter name and help text match the real event
  (retry exhaustion on the relevant request path), not an email-only interpretation.
- **AC-2:** Tests that assert metric text no longer depend on the misleading
  `email_notification_failures_total` name, unless a deprecated alias is kept and
  migration is documented.
- **AC-3:** Developer docs that referenced the old name are updated to the new
  contract, or they describe rename steps for consumers.
- **AC-4:** The change is traceable to PYPOST-402 TD-5 / PYPOST-422 without relying
  only on informal knowledge.

## Risks and assumptions

### Risks

- Existing Grafana or Prometheus rules use the old series name; renaming without
  notice can break alerts until dashboards are updated.
- Partial updates (code without docs, or the reverse) preserve confusion.

### Assumptions

- The increment still means “all retries exhausted” for the same request paths as
  today, unless another approved task changes behavior.
- Stakeholders accept that a rename may require a one-time update to monitoring
  configuration unless release materials document a transition period (for example
  dual export or a deprecated alias) and how long it lasts.
- Python remains the implementation language for `pypost` metrics (see below).

## Programming language determination

**Python.** The metric is registered and incremented in the `pypost` Python
package. Subsequent steps must follow `.cursor/lsr/do-python.md` alongside global
file rules.
