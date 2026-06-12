# PYPOST-383: Audit follow-up — full tree performance concerns

## Goals

The PYPOST-40 SOLID audit did not identify new performance-specific findings. Maintainers need
a single, traceable closure for the audit debt item so future readers know where collection-tree
scale risks are documented and which follow-up tickets already address them.

## User Stories

- As a **tech-debt owner**, I want the PYPOST-40 performance note closed with a clear verdict
  (no new audit findings; prior reports apply).
- As a **maintainer**, I want an inventory of collection-tree refresh paths (full vs incremental)
  so I can judge whether a UI change regresses scale behavior.
- As a **reviewer**, I want cross-links from `doc/dev/solid_audit.md` to the inventory and to
  existing Jira follow-ups (PYPOST-35, PYPOST-334, PYPOST-347, and related work).

## Definition of Done

- [x] PYPOST-40 performance debt item marked addressed in dev docs.
- [x] `doc/dev/collection_tree_performance.md` documents full vs incremental tree refresh paths.
- [x] Inventory cites prior tech-debt sources (PYPOST-35 and follow-ups).
- [x] Remaining full rebuild on regular save is documented as known, acceptable at current scale.
- [x] Automated test guards documented MainWindow signal wiring for save vs save-as paths.
- [x] Existing test suite passes.

## Task Description

**Source:** `ai-tasks/PYPOST-40/60-tech-debt.md` — "Performance Concerns / Prior reports cover
perf."

The audited codebase already had known collection-tree concerns (e.g. full tree reload on delete)
filed under PYPOST-35. Subsequent work added incremental delete (PYPOST-334), rename
(PYPOST-347), save-as insert (PYPOST-319), and index-assisted backend delete (PYPOST-340). This
task documents the current state and closes the audit item — it does not implement new
optimizations.

## Q&A

| Question | Answer |
| --- | --- |
| New performance fixes in scope? | No — document and cross-link only. |
| Is regular-save full refresh a blocker? | No — document as deferred; optimize only if profiling shows need. |
| Replace PYPOST-35 debt entries? | No — add audit-level summary that points to them. |
