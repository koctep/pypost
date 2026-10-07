# PYPOST-1266: Consistent collection import cancellation

## Goals

Make cancellation reliable for every supported collection file reader. A user who closes or
cancels an import should not receive different cancellation behavior merely because a different
reader was selected. Maintainers need an explicit, verifiable reader contract so replacement
readers and test substitutes cannot silently bypass cooperative cancellation.

The business reason comes from the cancellation guarantee gap recorded in
[PYPOST-1229 technical debt](../PYPOST-1229/60-tech-debt.md), follow-up item 1.

## User Stories

- As a user, I want a cancelled collection import to stop at its next safe processing checkpoint
  and discard its result, regardless of the supported reader used.
- As a maintainer, I want every production reader and test substitute to meet the same explicit
  cancellation requirements, so tests reflect the behavior shipped to users.
- As a user, I want successful imports and file errors to retain their existing behavior.

## Definition of Done

- Every supported reader used by background collection file import accepts the supplied
  cancellation checkpoint and permits it to stop processing cooperatively.
- Supported readers do not gain an alternative path that silently omits cancellation checkpoints.
  A reader that lacks the required capability is outside the supported contract.
- Cancellation requested during processing is honored at the next existing safe checkpoint.
  Cancellation before processing and before publication continues to suppress unwanted results.
- A cancelled import produces no successful result, applies no partial collections, and does not
  present cancellation as a file or parsing failure.
- Non-cancelled imports retain their candidate collections, per-record errors, file-level errors,
  and progress reporting.
- Automated contract checks demonstrate the supported reader variants and their cancellation
  behavior, including production integration and test substitutes. They also demonstrate that a
  reader lacking cancellation support cannot silently succeed through a compatibility path.
- Maintainers can identify the reader's required cancellation capability from its declared
  contract before using it in the import workflow.

## Task Description

Collection imports already support cooperative cancellation, but cancellation coverage depends
on the reader supplied to the background import operation. The existing compatibility behavior
can accept readers that offer no opportunity to observe cancellation until all reading returns.
This weakens the user expectation established by PYPOST-1229 and allows test substitutes to hide
that difference.

This task establishes one supported cancellation contract for collection import readers and
aligns the production path and its test substitutes with it. The implementation language is
Python. The detailed contract declaration, calling convention, and validation mechanism belong
to Step 2.

### Non-functional Requirements

- Preserve the responsive background import workflow and avoid forcible thread termination.
- Preserve the existing safe processing checkpoints; no whole-file cancellation latency bound
  is introduced by this task.
- Keep regression coverage deterministic with explicit test timeouts and bounded waits.

### Constraints and Scope

- Scope includes the collection file reader contract, its worker integration, production reader
  wiring, affected test substitutes, and focused contract coverage.
- Existing import initiation, conflict resolution, and application behavior remain the baseline
  for regression checks; redesigning those workflows is outside this task.
- Streaming input or interruptible file decoding belongs to PYPOST-1267. Changes to teardown
  wait policies belong to PYPOST-1264. Broader real-file cancellation coverage belongs to
  PYPOST-1265, except focused coverage needed to prove this contract.
- General compatibility with readers lacking cancellation capability is not required by the
  assigned issue. Such readers must be updated before use in this workflow.

## Main Entities

- **Collection import**: a user operation with a selected file and a processing outcome.
- **File reader**: a supported supplier of collection candidates, validation errors, and progress
  that participates in cooperative cancellation.
- **Cancellation request**: the user's decision to abandon an import before its result is used.
- **Processing checkpoint**: a safe opportunity for an active reader to observe cancellation and
  stop further work.
- **Import outcome**: successful candidates and errors, a file failure, or cancellation with no
  published candidates.

## Q&A

- **Why change the reader contract?** The assigned debt item identifies inconsistent cancellation
  coverage. An explicit contract prevents reader selection from weakening a user's cancel action.
- **Is immediate cancellation during file loading or decoding required?** No. That separate
  latency concern is tracked by PYPOST-1267; this task removes the supported-reader guarantee gap.
- **Must legacy readers without checkpoints remain supported?** No. The assigned issue requires
  production and test readers to accept the cancellation checkpoint.
- **Are additional stakeholder answers required?** No. The assigned issue and its originating
  debt item establish the business reason and scope; autonomous acceptance is owned by the
  sprint orchestrator.
