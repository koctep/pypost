# PYPOST-1426: Fault-Injection Test Suite for Flaky Networks and Corrupted Manifests

## Goals

Workspace users who import collection variables from remote libraries must keep a
stable, recoverable Import dialog when the network drops, a TCP stream resets
mid-transfer, or a remote catalog returns truncated or schema-invalid JSON. Today
clean timeout failures are covered, but maintainers lack automated proof that the
same non-modal error and retry path holds for flaky-network and corrupted-manifest
classes. This task closes that confidence gap so regressions cannot silently return
to modal crashes or silent empty tables.

Related debt: PYPOST-1415 Missing Tests (network partition / mid-stream termination;
malformed manifest streams). Transport abort from PYPOST-1425 is available for
cancel-during-transfer scenarios.

## Programming Language

- **Implementation language**: Python

## User Stories

1. As a workspace user on an unreliable network, when a remote collection fetch is
   reset or dropped mid-stream, I want a clear inline error and Retry option without
   losing the dialog or seeing a partial/corrupt variable table.
2. As a workspace user, when a remote catalog returns truncated JSON or a variable
   schema that fails validation, I want the same recoverable error UX so I can retry
   or pick another collection.
3. As a maintainer, I want automated tests that inject network drops, TCP resets,
   partial JSON, and malformed variable schemas so those contracts stay green in CI.
4. As a maintainer, when I cancel during a flaky mid-stream transfer, I want abort
   behavior (PYPOST-1425) to remain quiet and prompt rather than surfacing a false
   fetch failure.

## Definition of Done

- Automated tests simulate network drop / connection reset mid-stream for remote
  collection import and assert dialog stays open with inline error + retry and an
  empty (non-partial) table.
- Automated tests feed truncated / invalid JSON and malformed variable schema
  payloads through the remote fetch path and assert the same recoverable UX (no
  crash, no silent success with bad data).
- Cancel during a simulated mid-stream transfer continues to honor transport abort
  without presenting a user-facing fetch failure for the cancelled generation.
- Existing timeout/retry and virtualization coverage remains intact.
- New tests declare explicit pytest timeouts per project testing rules.

## Task Description

Import Collection Variables already handles clean `TimeoutError` with an inline
banner and retry. Fault classes that matter in real remotes — TCP reset / connection
drop mid-payload, partial JSON manifests, and schema-violating variable records —
lack dedicated automated cases. This task adds that fault-injection suite against
the remote collection import path, using transport abort where cancel intersects a
flaky transfer.

## Q&A

- **Q:** Is this a new product feature or proof of existing recovery?
  **A:** Primarily automated proof and hardening of recovery contracts for flaky and
  corrupt remotes; any gap found during repro is fixed as part of the suite work.
- **Q:** Live network dependencies?
  **A:** No — inject faults via test doubles / local harness without external services.
- **Q:** Programming language?
  **A:** Python (PySide6 Qt UI + library service path), matching existing import tests.
