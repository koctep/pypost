# PYPOST-1337: Trustworthy live type-quality gate outcomes

## Goals

Developers and CI maintainers need type-quality feedback that distinguishes valid analysis
from unavailable or untrustworthy diagnostics. Restore confidence in the live baseline gate
without silently accepting a failed tool or deleting known debt without evidence.

## User Stories

- As a developer, I can tell whether type analysis completed reliably and whether a failure
  comes from new type findings, existing debt changes, or unavailable tooling/diagnostics.
- As a reviewer, I can trust a clean result and assess any baseline reconciliation against
  evidence that the recorded findings were actually resolved.
- As a CI maintainer, I receive an actionable failure when type analysis cannot be trusted,
  rather than an apparent disappearance of all known findings.
- As a maintainer, I can preserve the existing policy that new type debt fails the gate while
  handling genuinely resolved debt deliberately.

## Definition of Done

1. The reported zero-current-versus-181-known discrepancy has an evidence-backed explanation.
   The correction addresses that identified cause within this issue's scope.
2. The normal type-quality workflow distinguishes successful analysis from tool execution,
   prerequisite, or diagnostic interpretation failures. Invalid analysis produces a failing,
   actionable outcome and cannot masquerade as a valid clean run.
3. Valid analysis retains the existing protection against new type findings and reports known
   or resolved debt consistently. A genuinely clean result can succeed once the expected
   baseline has been deliberately reconciled with trustworthy evidence.
4. Baseline reconciliation, if required by the investigation, does not accept new debt or
   discard existing entries solely because an invalid run yielded no recognized findings.
   Invalid analysis leaves the recorded baseline intact.
5. Automated regression coverage demonstrates the identified defect and protects the distinction
   between valid results and failed or uninterpretable analysis without external service reliance.
6. The existing live gate regression and normal Make type-quality checks succeed, apart from
   unrelated baseline failures identified with reproducible evidence under sprint triage.
7. Existing production quality scope, behavioral assertions, test inclusion, and timeout
   protections remain effective. Developers can understand failure categories and any supported
   baseline maintenance policy from the project documentation.

## Task Description

### Problem and evidence

The live regression `tests/test_mypy_baseline_live.py::test_mypy_baseline_live_gate_passes`
fails when the checker reports zero current findings against a baseline containing 181 entries.
The supplied isolated run at commit `36d7782b` reproduced checker exit 1 and all 181 entries
reported as resolved. This establishes a pre-existing discrepancy, not its cause.

Tool execution failure, missing prerequisites, diagnostic interpretation, dependency/stub
changes, and an outdated baseline are investigation possibilities. None is established by the
observed count alone. The current task base is `103fe81a`.

### Business reason

Type-quality gates should provide trustworthy evidence about application quality and known
debt. A failed or misinterpreted analysis can make old findings appear resolved, undermining
review confidence and risking loss of the baseline. Conversely, a genuinely clean valid run
should not remain permanently blocked by obsolete entries after justified reconciliation.

### Implementation language

Python.

### Scope

- Investigation of the reported live type-quality result and its recorded baseline discrepancy.
- Narrow correction of the identified gate/tooling/diagnostic or baseline maintenance defect.
- Regression verification of valid results, invalid analysis, and safe reconciliation if needed.
- Documentation of actionable outcomes and the supported baseline maintenance policy.

### Out of scope

- Blind deletion or regeneration of the 181-entry baseline to obtain a passing result.
- Accepting additional type debt or reducing the existing analysis scope.
- Broad application refactoring, unrelated type repairs, or arbitrary dependency upgrades.
- Suppressing the live regression, relaxing test deadlines, or weakening normal quality gates.

### Functional requirements

- A type-quality result states whether analysis was trustworthy before interpreting debt changes.
- Failed or uninterpretable analysis yields a nonzero outcome with enough context to investigate.
- Valid known findings remain distinguishable from new and genuinely resolved findings.
- Invalid analysis does not alter the recorded baseline or produce an apparent clean pass.
- Any reconciliation is supported by a successful analysis and a deliberate maintenance action;
  it preserves protection against new debt.

### Non-functional requirements and constraints

- Verification remains repeatable, with finite test and subprocess protections.
- Repository build, analysis, test, dependency, and artifact-verification operations use Make.
- Preserve unrelated files, completed task records, and existing production quality coverage.
- Scope remains limited to this Jira debt issue and the evidence-backed cause of the discrepancy.
- Do not assume the count of parsed findings alone proves that the analysis completed correctly.

### Main entities

- **Analysis run**: a type-quality attempt with a trustworthy completion outcome or a failure.
- **Type finding**: an actionable issue reported by a valid analysis of the expected source scope.
- **Known-debt baseline**: reviewed recorded findings against which new and resolved debt compare.
- **Maintenance decision**: a deliberate, evidence-backed reconciliation of genuinely resolved debt.
- **Quality-gate consumer**: a developer, reviewer, or CI process using the outcome to assess changes.

## Q&A

- **Why investigate before changing the baseline?** Zero recognized findings may indicate either
  a valid clean run or a failure; the current evidence does not distinguish those explanations.
- **Must the baseline retain 181 entries permanently?** No. Genuinely resolved findings may be
  reconciled after valid analysis and review; invalid analysis must not justify removing them.
- **Is a dependency upgrade prescribed?** No. Any dependency-related correction must follow the
  investigated cause and remain narrowly justified within the issue.
- **Who accepts these requirements?** The autonomous sprint orchestrator after independent review.
