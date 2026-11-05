# PYPOST-1427: Paged Model Virtualization for Extreme Collections

## Goals

Operators and power users who import collection variable catalogs with tens of
thousands of entries need the import inspector to open instantly and stay light
on memory. Today the virtualized table already avoids per-row widgets, but the
model still materializes a full in-memory row record for every variable at load
time. At 50,000–100,000 variables that eager materialization costs tens of
megabytes and adds a noticeable pause on the UI thread before the first paint.

This task delivers incremental, on-demand population of the collection-variables
table model so extreme catalogs load immediately, keep model memory overhead
well under a fixed budget, and still present correct selection, conflict
strategy, and summary behavior for the full catalog.

Related origin: `ai-tasks/PYPOST-1415/60-tech-debt.md` follow-up #5
(Paged / Chunked Model Virtualization). Model location after PYPOST-1423:
`pypost/ui/models/collection_variables_table_model.py`.

## Implementation Language

- **Implementation language**: Python

## User Stories

- As a **workspace operator importing a huge collection**, I want the variables
  table to appear immediately after the collection is available so I am not
  blocked by a long model-build pause.
- As a **desktop user on a memory-constrained machine**, I want the import
  inspector’s model overhead for extreme catalogs to stay modest (sub-10MB
  model working set for row state) so the app remains responsive.
- As an **operator reviewing conflicts**, I want scrolling, selection, conflict
  strategy changes, bulk actions, and the import summary to remain correct
  across the full catalog even when only a window of rows is materialized.
- As a **QA / maintainer**, I want automated coverage that proves instant load,
  bounded cache size, and behavioral parity for small catalogs so regressions
  are caught in CI.

## Definition of Done

1. Loading a collection into `CollectionVariablesTableModel` does **not**
   eagerly allocate one row record per variable for the entire catalog.
2. Initial model load for a 50,000-variable catalog completes without a
   multi-hundred-millisecond UI-thread materialization loop (instant initial
   load relative to today’s full-list build).
3. Model working memory for materialized row records stays bounded
   (sub-10MB overhead target for the model’s cache/window of records) while
   still serving viewport/cursor access for 50k–100k catalogs.
4. Selection toggles, conflict strategies, bulk select/strategy, preset
   candidate updates, and summary/selected-key APIs remain correct for the
   full logical row set.
5. Existing import-dialog / virtualization / related UI tests remain green;
   small-catalog behavior is unchanged from the user’s perspective.
6. Automated repro/regression tests cover extreme-catalog load latency,
   bounded materialization, and correctness after sparse access / eviction.

## Task Description

**Problem:** PYPOST-1415 virtualization removed widget cost but left an
eager `list[CollectionVariableRowRecord]` that scales linearly with catalog
size (~25–50MB and 150–250ms main-thread work at 50k–100k rows).

**Outcome:** The model reports the full logical row count immediately, fetches
or builds row state in chunks/cursor windows as the user (or tests) touch rows,
keeps only a bounded window of materialized records, and preserves import
decision state across the whole catalog.

**Out of scope:** Changing how collections are fetched from disk/network,
rewriting the dialog layout, socket-level abort, fault-injection suites, and
async connection discovery (other PYPOST-142x tickets). Replacing the
underlying `Collection.variables` storage format is out of scope; this task
bounds the **table model’s** eager record graph.

## Q&A

- **Q:** Why is this a product need and not only an internal refactor?
  **A:** Extreme catalogs currently impose a visible load hitch and large
  memory spike before the inspector is usable; operators need instant first
  paint and bounded overhead.
- **Q:** Must every historical row remain editable after scrolling away?
  **A:** Yes — selection and conflict strategy decisions must survive cache
  eviction and still feed import summary / apply.
- **Q:** Does “sub-10MB” include the deserialized `Collection` itself?
  **A:** No — it targets the model’s incremental record/cache overhead beyond
  the already-loaded collection domain objects.
