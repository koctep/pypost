# PYPOST-1265: Expand collection import cancellation coverage

## Goals

Give maintainers regression coverage that proves a cancelled collection file import behaves
the same way at every point where cancellation can happen. A cancelled import must stop its
background work, report one cancellation outcome and nothing else, and leave the user's
collections unchanged. Future changes must not break any of these points without a failing
test.

The business reason is follow-up 3 of
[PYPOST-1229 technical debt](../PYPOST-1229/60-tech-debt.md). Later debt notes confirmed and
narrowed it: [PYPOST-1266](../PYPOST-1266/60-tech-debt.md),
[PYPOST-1267](../PYPOST-1267/10-requirements.md) and
[PYPOST-1264](../PYPOST-1264/60-tech-debt.md) (shortcut 2: the cancellation regression's
in-flight margin is covered by this issue). The issue is debt for the sprint goal "typed
cancellation protocols, responsive decoding interruption, robust teardown lifecycle". Three of
the four items the ticket names have been fully or partly delivered by later work since the
ticket was written. This task covers only what is still missing and does not duplicate
existing coverage.

## User Stories

- As a user who cancels or closes an import right after it starts, I want no collections
  added and no error shown, even though no file content has been processed yet.
- As a user who cancels a YAML import while its collections are being validated, I want the
  same outcome as for JSON: the import stops and nothing is applied.
- As a maintainer, I want every cancellation regression to check the exact number of
  cancellation, completion and failure outcomes, so a duplicate or missing outcome fails a test.
- As a maintainer, I want the in-flight cancellation regressions to prove that cancellation
  stopped the work, not that the work happened to finish within a time margin.

## Coverage Map

The ticket names four items. Each is mapped to the current suite (HEAD `2703575a`).

| # | Ticket item | Status | Evidence |
| - | ----------- | ------ | -------- |
| 1a | Real JSON input, record-level cancellation | **Already covered** | `tests/test_collection_import_reader_contract.py::test_production_json_reader_contract` (real temp JSON file; cancel at records 1 and 2; one cancellation, no completion, no failure) |
| 1b | Real JSON/YAML input, cancellation during file loading/decoding | **Already covered** (PYPOST-1267, `6c39e40f`) | `tests/test_collection_import_decode_cancellation.py::test_cancellation_during_real_file_loading[json/yaml/fallback]` and `::test_cancellation_during_active_lexical_scanning[*]` (16 MiB files, exactly one cancellation, ≤ 1000 ms) |
| 1c | Real YAML input, record-level (validation-phase) cancellation | **Remaining gap** | No worker-level test cancels a real YAML file at a collection-record checkpoint. YAML coverage exists only for decoding (1b) and the decoder unit tests. |
| 2 | Pre-start interruption | **Remaining gap** | The worker checks for interruption before reading, but no test exercises that check. No test sends a cancellation before the reader is called and then checks the outcome. |
| 3a | Exact signal counts, newer regressions | **Already covered** | Reader-contract, progress (legacy rejection), decode-cancellation and `test_final_publication_guard_discards_result_after_last_checkpoint` assert exact outcome lists. |
| 3b | Exact signal counts, original PYPOST-1229 regressions | **Remaining gap** | `tests/test_collection_import_cancellation_repro.py::test_worker_stops_promptly_when_interrupted_mid_parse` only checks completion and failure flags and never checks for a cancellation outcome. `::test_teardown_worker_stops_after_interruption` and `::test_default_teardown_requests_interruption_before_wait_and_discards_result` check logs and side effects but never count outcomes. |
| 4a | "Supported legacy reader without `on_progress`: cancellable only before/after reading" | **Obsolete** | PYPOST-1266 (`0345e88c`) removed the compatibility fallback. A reader without the cancellation checkpoint is no longer supported. Restoring this contract is out of scope (PYPOST-1266 debt note). |
| 4b | Legacy reader is rejected (replacement contract) | **Already covered** | `tests/test_collection_import_progress.py::test_collection_import_parse_worker_rejects_legacy_single_arg_reader` (reader body never runs; one failure; no completion or cancellation; ERROR log captured) and the supported shapes in `tests/test_collection_import_reader_contract.py::test_supported_reader_shapes` |
| 5 | Explicit timeout markers and bounded waits | **Ongoing constraint** | Each affected module has a module-level `pytestmark` timeout (30 s, 60 s, 150 s). New or changed coverage must keep this. |
| 6 | Cancellation repro in-flight margin (from PYPOST-1264 debt, shortcut 2) | **Remaining gap** | `_TEARDOWN_WAIT_IDLE_MS` went from 150 to 1000 ms against a reader that takes about 2 s. The default-budget (5000 ms) teardown regression never shows that the reader was stopped before it processed all records. |

## Definition of Done

1. **Pre-start cancellation.** An automated regression covers a cancellation that arrives
   after an import has been requested but before the file reader starts. It shows that:
   the reader does not process any record; there is exactly one cancellation outcome; there
   is no completion outcome and no failure outcome; no collections are applied; and the
   background work has finished when the test ends. The regression must actually reach the
   worker's "before reading" decision, not the in-flight checkpoint.
2. **Real YAML record-level cancellation.** An automated regression imports a real temporary
   YAML collection file through the background import. It cancels at a collection-record
   checkpoint, after decoding has finished. It shows exactly one cancellation outcome, no
   completion or failure, and that no later records are reported. A run of the same file
   without cancellation shows the expected candidates, validation errors and progress, as
   the JSON contract test does today.
3. **Exact outcome counts in the original regressions.** The in-flight worker regression and
   both teardown regressions in `tests/test_collection_import_cancellation_repro.py` check
   the exact number of each outcome: one cancellation, zero completions, zero failures.
   Flag-only or log-only checks are not enough.
4. **In-flight proof without a timing margin.** The teardown regressions show that
   cancellation stopped the reader before it processed all records, for both the explicit
   1000 ms budget and the default budget. They must not rely only on "the budget is shorter
   than the reader's total run time". A much faster reader or a much slower runner must make
   the test fail or keep it valid; it must never pass falsely.
5. **No regressions in existing coverage.** Every existing test listed as "Already covered"
   in the coverage map keeps passing and keeps its current assertions. The removed legacy
   compatibility contract is not restored.
6. **Explicit timeouts and bounded waits.** Every new or changed test has an explicit
   `pytest.mark.timeout` (module, class or function). Every internal wait (thread joins,
   events, event-loop polling) has a finite limit. Every test stops its background worker
   before it ends, whether it passes or fails.
7. **Validation.** `make test` shows the new and changed regressions passing. Pre-existing
   unrelated failures are reported with their Jira IDs, not fixed here.
   `make verify-ai-tasks` passes.

## Task Description

Collection file import runs in the background and supports cooperative cancellation. Several
tasks have strengthened it: PYPOST-1229 added checkpoint cancellation, PYPOST-1266 requires
typed cancellation-aware readers, PYPOST-1267 added cancellation during loading and decoding,
and PYPOST-1264 put teardown under one lifecycle policy. Each task added focused tests. What
is left is a few uncovered points in the cancellation lifecycle and some older regressions
with weaker assertions than the newer ones.

The implementation language is Python. This is a test-coverage task. No change to user-visible
behavior is expected. If a new regression shows that a production path does not behave as
required, record it as a finding for Step 2 or Step 3. Do not widen this task's scope without
a decision.

### Non-functional Requirements

- Tests must be deterministic. Cancellation is triggered from observed checkpoints or explicit
  synchronization, not from sleeps chosen to beat a race.
- Tests must not take much longer to run. New regressions use small fixture files. Large-file
  latency coverage stays in PYPOST-1267's module.
- New error-path tests follow the project's `caplog` contract (do-testing C1–C5).

### Scope

In scope:

- Collection file import cancellation through the background parse worker and the import
  actions' teardown, for the gaps marked "Remaining gap" in the coverage map.
- Stronger assertions in the existing PYPOST-1229 cancellation regressions.

Out of scope:

- Restoring or documenting support for readers without the cancellation checkpoint
  (obsolete since PYPOST-1266).
- Large-file loading and decoding latency (covered by PYPOST-1267).
- Teardown budget arithmetic and policy values (covered by PYPOST-1264 tests). Main-window
  shutdown registration (PYPOST-1321) and the nested worker-finish join test (PYPOST-1322).
- Cancellation of connected-library import (PYPOST-1324). Cancellation after collection
  application has begun (the APPLYING state).
- Live-logging timing problems under `make test` (PYPOST-1326). Production code changes,
  unless a new regression proves a defect and that is accepted at a later step.

## Main Entities

- **Collection import**: a user operation that turns a selected JSON or YAML file into
  candidate collections.
- **Cancellation request**: the decision to abandon an import, from the user, panel teardown
  or a test.
- **Cancellation point**: when the request arrives. Before reading starts, during loading or
  decoding, at a collection-record checkpoint, or after the last checkpoint but before the
  result is published.
- **Import outcome**: exactly one of completion (candidates and validation errors), failure, or
  cancellation. A cancelled import publishes no candidates and applies no collections.
- **File reader**: a supported, cancellation-aware supplier of candidates (PYPOST-1266
  contract).

## Q&A

- **Why is the legacy-reader item not implemented as written?** The ticket asked to document
  that a reader without `on_progress` "can only be cancelled before parsing starts or after
  the reader returns". PYPOST-1266 (`0345e88c`) made such readers unsupported and rejected.
  `test_collection_import_parse_worker_rejects_legacy_single_arg_reader` already covers that
  rejection, so this item is obsolete and needs no new work.
- **Why is real JSON/YAML only partly in scope?** Real JSON at record checkpoints (PYPOST-1266)
  and real JSON and YAML during loading and decoding (PYPOST-1267) are already covered. Only
  YAML at the record-validation checkpoint is still missing.
- **Why include the in-flight margin?** PYPOST-1264's debt analysis (shortcut 2) explicitly
  assigns the reduced in-flight margin of the cancellation regression to this issue rather
  than a new ticket.
- **Are user-close (panel close) matrices in scope?** Only through the existing teardown entry
  point. Application shutdown does not yet tear down collection import (PYPOST-1321), so that
  path cannot be covered here.
- **Open question for Step 2:** how can a test reliably reach the worker's "before reading"
  check? Qt may clear an interruption request when a thread starts, so a request made before
  start may not reach that check. Step 2 must choose an approach that does reach it, without
  changing production behavior. This document does not prescribe the approach.
- **Are stakeholder answers needed?** No. The assigned issue, its source debt item and the
  later debt notes give the business reason and scope. Acceptance belongs to the autonomous
  orchestrator after independent review.
