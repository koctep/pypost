# PYPOST-1194: Raise SOLID FILE_CAPS for collections_presenter and tabs_presenter LOC drift

## Goals

Maintainers rely on the SOLID audit baseline as a trustworthy quality signal:
monitored modules must stay within declared line-of-code caps, and the inventory
test must stay green when growth is intentional. Today that gate fails because
`collections_presenter` and `tabs_presenter` exceed their declared caps after
legitimate presenter growth. This debt item restores a green, accurate inventory
signal by aligning those caps with current measured size (repository ~10%
headroom policy), without changing end-user product behavior.

**Business goal**: Keep the SOLID FILE_CAPS inventory gate trustworthy for CI
and maintainers after intentional presenter growth, so Suite Failures Cleanup
can clear this pre-existing red path without blocking unrelated work.

**Implementation language**: Python (audit metrics script, baseline snapshot,
pytest solid-audit guard; no new runtime language).

## User Stories

- As a **maintainer or CI runner**, I want
  `test_audit_module_inventory_within_caps` to pass when monitored presenters
  have grown intentionally within policy headroom, so a red suite means a real
  regression rather than stale caps.
- As a **developer extending collections or tabs presenters**, I want published
  FILE_CAPS to reflect current accepted size with modest headroom, so I know
  when further growth needs extraction or an explicit cap review.
- As a **Suite Failures Cleanup stakeholder**, I want this pre-existing failure
  (surfaced during PYPOST-1192 at base `18a4d9d1`) closed so the sprint goal is
  complete.

## Definition of Done

- `collections_presenter.py` and `tabs_presenter.py` inventory caps are raised
  (or modules reduced) so measured LOC is within caps under the project’s
  ~10% headroom policy for intentional growth.
- Cap rationale is documented beside the updated entries (ticket / measured
  baseline).
- Baseline snapshot is regenerated and kept in sync with the generator.
- The following check passes under the documented repro:

  - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_audit_module_inventory_within_caps`

- Repro command remains green:

  `make test PYTEST_ARGS="tests/test_solid_audit_baseline.py"`
- Failures are not “fixed” by skipping, xfailing, or deleting the named test.
- Sibling Suite Failures Cleanup items already Done (1181, 1193, 1195, 1196)
  remain out of scope; no product behavior changes for collections/tabs UX.

## Task Description

### Problem

The SOLID audit inventory guard fails because measured lines exceed declared
`FILE_CAPS`:

- `collections_presenter.py`: 486 lines vs cap 403
- `tabs_presenter.py`: 1059 lines vs cap 785

Confirmed pre-existing at base commit `18a4d9d1` during PYPOST-1192 (NON-BLOCKER
tech debt). Related to but distinct from PYPOST-1111 (different node id).

### Business need

Operators and CI cannot trust the solid-audit inventory gate while caps lag
intentional growth. Raising caps (preferred when architecture accepts the
growth) restores the signal; large extractions are deferred unless architecture
chooses that path.

### Scope

**In scope**

- Align FILE_CAPS for the two drifted presenter modules (and regenerate
  baseline / docs as required by solid-audit maintenance).
- Make the named inventory test green.

**Out of scope**

- Product feature work in collections/tabs UI.
- Sibling sprint failures already ticketed/done elsewhere.
- Broad SOLID refactor of all oversized modules.

## Constraints and Assumptions

- Prefer raising caps with ~10% headroom for intentional growth (ticket
  guidance); extraction only if architecture prefers it for these modules.
- Use `make` targets only for test/lint/check.
- Do not skip or delete the inventory test.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| FILE_CAPS inventory | Declared size limits for monitored modules |
| Collections presenter | UI presenter for collections (drifted LOC) |
| Tabs presenter | UI presenter for workspace tabs (drifted LOC) |
| Solid audit baseline test | Automated guard that measured LOC ≤ cap |

## Q&A

| Question | Answer |
| --- | --- |
| Raise caps or extract? | Typically raise caps for intentional growth (ticket default). |
| Change user-visible behavior? | No. |
| Pre-existing? | Yes — at `18a4d9d1`, found during PYPOST-1192. |
