# PYPOST-1425: Low-Level Socket and HTTP Request Abort in Collection Fetch

## Goals

When a user cancels a remote collection load (or catalog discovery) in the Import
Collection Variables dialog, the product should stop spending network bandwidth and
background worker time on that request. Today, cancel only discards the eventual
result: the background work may keep reading until the remote I/O finishes or times
out. Users who rapidly change selections or close the dialog should not wait on
orphaned I/O, and shared environments should not burn capacity on abandoned fetches.

Related debt: PYPOST-1415 (fetch cancel) and PYPOST-1424 (discovery cancel mirrors the
same pattern).

## Programming Language

- **Implementation language**: Python

## User Stories

1. As a workspace user, when I cancel a slow remote collection load, I want the
   background work to stop promptly so the dialog stays responsive and I am not
   waiting on an abandoned transfer.
2. As a workspace user who quickly switches between remote collections, I want each
   superseded fetch to release its transport resources so only the current selection
   consumes network and worker capacity.
3. As a workspace user who closes or dismisses the Import dialog during catalog
   discovery, I want discovery I/O to abort as well so dialog teardown does not stall
   on remote listing work.
4. As a maintainer, I want automated proof that cancel aborts in-flight transport work
   rather than only ignoring the late result.

## Definition of Done

- Cancelling an in-flight remote collection fetch aborts the underlying transport work
  (not only generation-discard of the result).
- The fetch worker exits promptly after cancel instead of waiting for the full remote
  read or timeout where abort is supported.
- Where practical, ManifestDiscoveryWorker cancel uses the same transport-abort
  behavior for connection/manifest listing I/O.
- Automated tests demonstrate abort-on-cancel for fetch (and discovery where covered).
- Existing import-dialog virtualization, generation discard, async discovery, and
  remote-fetch UX remain intact.
- Cancelled operations do not surface as user-facing fetch/discovery failures.

## Task Description

Import Collection Variables already loads remote collections and discovers catalogs on
background threads with UI cancel and generation-based discard. Cancel does not yet
stop the in-flight I/O itself, so cancelled work can still consume bandwidth and worker
time until the remote call returns. This task closes that gap for collection fetch and
extends the same abort behavior to manifest discovery where practical.

## Q&A

- **Q:** Why is generation discard not enough?
  **A:** Discard protects UI correctness but leaves the remote read running; users still
  pay latency and resource cost for abandoned work.
- **Q:** Does discovery need the same treatment?
  **A:** Yes where practical — PYPOST-1424 notes discovery cancel mirrors fetch and can
  stall dialog close for up to the wait budget when listing ignores interruption.
- **Q:** Programming language?
  **A:** Python (PySide6 Qt UI), matching existing workers and library service.
