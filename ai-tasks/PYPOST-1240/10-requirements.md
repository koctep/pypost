# PYPOST-1240: Give bare ownership diagnostics a module name and remedy

## Goals

Make ownership-validation failures useful to the maintainer who first sees them in a local or CI
quality-gate result. When an expected ownership responsibility is missing, the diagnostic must
name the responsible module and tell the maintainer what needs to be restored.

The business reason is rapid, accurate repair. A bare “missing X” message forces a maintainer to
search for where the responsibility belongs and what it should provide. A self-describing
diagnostic directs the repair immediately and reduces the risk that the failure is mistaken for an
unrelated missing responsibility.

This is a diagnostic-quality improvement. It does not change ownership decisions, lookup results,
selection outcomes, or application behavior.

## User Stories

- As a maintainer responding to a failed quality gate, I want an ownership diagnostic to identify
  the responsible module so that I can open the correct product area immediately.
- As a maintainer, I want the diagnostic to state the intended remedy so that I can restore the
  missing ownership responsibility without reverse-engineering the failure.
- As a reviewer, I want the diagnostic to distinguish ownership failures from unrelated missing
  responsibilities so that the failure is triaged against the correct area of responsibility.
- As a CI consumer, I want the diagnostic to remain clear and consistent so that I can understand
  the problem from the reported failure alone.

## Definition of Done

- **AC-1 — Recursive lookup ownership is identified:** If the recursive/tree lookup responsibility
  is missing, the diagnostic names the Tree Index module, identifies the missing responsibility,
  and directs the maintainer to restore recursive lookup there.
- **AC-2 — Item-view selection ownership is identified:** If the item-view selection responsibility
  is missing, the diagnostic names the UI Actions module, identifies the missing responsibility,
  and directs the maintainer to restore item-view selection there.
- **AC-3 — Remedy is actionable:** Each diagnostic gives a maintainer enough direction to determine
  where the missing responsibility belongs and what responsibility must be restored; it is not
  merely a longer restatement of “missing X.”
- **AC-4 — Ownership context is unambiguous:** The wording makes the responsible module and its
  ownership responsibility distinguishable from unrelated missing responsibilities.
- **AC-5 — Diagnostic is readable at a glance:** The missing responsibility, responsible module,
  and actionable remedy appear together on one readable line.
- **AC-6 — No behavior change:** Existing ownership rules, lookup results, selection behavior,
  application behavior, and aggregate failure reporting remain unchanged.
- **AC-7 — Focused scope:** The work is limited to the two affected ownership diagnostics and the
  requirements for their observable diagnostic experience; no unrelated product changes are
  included.

## Task Description

The current ownership-validation experience identifies flat lookup, recursive/tree lookup, and
item-view selection responsibilities. Two missing-responsibility cases currently report only the
missing name: recursive lookup and item-view selection. A maintainer reading either failure must
otherwise infer the responsible module and the intended correction.

The task makes those failures self-describing. The desired outcome is that a maintainer can move
from a failed diagnostic to the correct module and repair direction without confusing the failure
with an unrelated missing responsibility. The change is limited to the diagnostic experience and
does not redefine ownership or alter product behavior.

**Programming language:** Python.

### In Scope

- Improving the two known bare missing-responsibility diagnostics for recursive lookup and item-view
  selection.
- Naming the Tree Index module as the owner of recursive/tree lookup.
- Naming the UI Actions module as the owner of item-view selection.
- Stating the responsibility to restore in each diagnostic.
- Keeping the missing responsibility, owner, and remedy together on one readable line.

### Out of Scope

- Changing the ownership policy or deciding which module owns a responsibility.
- Changing lookup, traversal, selection, or other application behavior.
- Adding new ownership responsibilities or product capabilities.
- Reworking unrelated diagnostics or broadening the task beyond the two identified cases.

### Constraints and Assumptions

- The existing ownership assignments remain authoritative: recursive/tree lookup belongs to the Tree
  Index module, and item-view selection belongs to the UI Actions module.
- Each failure must communicate its missing responsibility, owner, and remedy in one readable line.
- The same missing-responsibility condition produces consistent wording in local and CI quality-gate
  results.
- The task concerns diagnostic communication only; no application runtime behavior is expected to
  change.

## Main Entities and Interactions

- **Ownership responsibility:** A product responsibility such as recursive lookup or item-view
  selection that must be provided by one responsible module.
- **Owning module:** The product module responsible for providing the named ownership responsibility
  and the maintainer’s repair destination when it is missing.
- **Missing-responsibility condition:** A validation condition indicating that an expected ownership
  responsibility is absent.
- **Ownership diagnostic:** The failure message presented to a maintainer. It identifies the missing
  responsibility, its owning module, and the corrective direction.
- **Quality-gate consumer:** A maintainer or reviewer who uses the diagnostic to classify and repair
  the failure.

The interaction is: ownership validation identifies an absent responsibility; the resulting
diagnostic names the owning module and remedy; the quality-gate consumer uses that information to
repair the correct responsibility and distinguish the failure from unrelated missing
responsibilities. If the responsibility is present, the existing ownership validation continues to
report success under the existing rules.

## Non-Functional Requirements

- **Clarity:** A maintainer unfamiliar with the immediate context can identify the responsible
  module, missing responsibility, and repair direction from the failure alone.
- **Consistency:** The same missing-responsibility condition communicates the same owner and remedy
  in local and CI quality-gate results.
- **Readability:** The owner, missing responsibility, and remedy are presented together on one
  readable line.
- **Low risk:** No material performance, stability, security, or application-user impact is
  introduced because the change concerns diagnostic communication only.
- **Maintainability:** The wording uses plain language consistent with the ownership vocabulary and
  remains actionable without requiring the maintainer to search unrelated product areas.

## Q&A

**Q: Why is this needed if ownership validation already finds the problem?**

A: Finding a problem is not enough if the failure does not identify who owns the missing
responsibility or how to repair it. Self-describing diagnostics shorten triage and prevent the
failure from being mistaken for an unrelated missing responsibility.

**Q: Which missing responsibilities are covered?**

A: The recursive/tree lookup responsibility owned by the Tree Index module and the item-view
selection responsibility owned by the UI Actions module.

**Q: Does this change application behavior?**

A: No. It changes the information provided by ownership-validation failures while preserving the
existing ownership rules, lookup behavior, selection behavior, and validation outcomes.

**Q: Why must the wording remain on one line?**

A: Keeping the missing responsibility, owner, and actionable remedy together lets a maintainer
understand and act on the failure without searching elsewhere.

**Q: Which language governs the task?**

A: Python.
