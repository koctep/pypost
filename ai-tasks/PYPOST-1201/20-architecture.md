# PYPOST-1201: Optional shared silent transport test support

## Research

### Accepted requirements and Jira scope

The accepted requirements make reuse conditional. Shared support is justified only
by a second relevant UI scenario needing materially the same silent transport
behavior, or by meaningful duplication that could diverge. Jira describes the
change as an optional extraction and excludes production behavior changes.

Sources:

- [Accepted requirements](10-requirements.md)
- [PYPOST-1201 in Jira](https://pypost.atlassian.net/browse/PYPOST-1201)

### Repository evidence

- `tests/test_websocket_client_ui_repro.py` contains the only discovered silent
  transport definition and its consumers. The helper is used by two tests in the
  same WebSocket UI lifecycle module: one exercises connect/disconnect controls,
  and one protects the Open state from a deferred failure after event pumping.
- The helper is tailored to the UI-controller seam: it records the handshake
  target, implements the transport protocol's command surface as no-ops, and
  deliberately emits no listener callbacks.
- `tests/test_websocket_session_controller.py` and
  `tests/test_websocket_session_engine_repro.py` contain other transport doubles,
  but they exercise controller or engine protocol behavior rather than the same
  silent UI lifecycle scenario. Similar naming is not evidence of interchangeable
  responsibilities.
- No second UI test module currently consumes the silent behavior, and the two
  same-module call sites do not constitute a separate consumer boundary.

The repository therefore does not meet the reuse threshold. The current local
support remains the smallest dependency surface that preserves the existing test
intent.

### Relevant Python guidance

If a future shared helper is justified, its type boundary can remain narrow and
structural rather than coupling consumers to a concrete production class. Python's
official documentation describes `typing.Protocol` as the mechanism for structural
subtyping, while `unittest.mock` documents test doubles as replacements for system
components. These references inform the future seam; they do not require a new
abstraction for this task.

- [Python `typing.Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [Python `unittest.mock`](https://docs.python.org/3/library/unittest.mock.html)

## Implementation Plan

This step produces an architecture decision record only. No production code,
tests, or shared test module is added while the threshold is unmet.

1. Retain the existing file-local silent transport double in its current UI test
   module. Keep its explicit factory injection and hermetic no-callback behavior.
2. Record the current consumer inventory and the retain-local decision in the
   task artifacts so a later consumer can revisit the choice.
3. Re-evaluate the decision when a distinct relevant UI scenario appears or when
   the existing support is duplicated enough to create a credible drift risk.
4. If the threshold is met, introduce one test-only support module and migrate
   only the qualifying UI consumers. Preserve behavior with focused lifecycle
   assertions before considering any broader cleanup.

**Mandatory — Failing Repro (next Step 3):** N/A — no behavioral change is
planned. This architecture retains existing test support and changes neither
production runtime behavior nor the WebSocket protocol. Step 3 should remain
`N/A — no behavioral change` unless repository evidence changes and a shared
support migration becomes necessary.

## Architecture

### Current module diagram and decision

```text
WebSocket UI lifecycle tests
        |
        | explicit transport-factory injection
        v
WebSocketSessionController ----> file-local silent transport double
        |                          (no network, no callbacks)
        v
WebSocketPresenter / WebSocketTab

Production transport remains the controller's normal runtime dependency and is
outside this test-support decision.
```

The selected pattern is dependency injection with a test double at the existing
controller factory boundary. The local helper is owned by the test module that
defines the UI lifecycle contract. The controller owns transport creation and
consumes only the established transport protocol; it does not know whether the
factory returns a production transport or a test double. UI presenters and tabs
own assertions and event driving, not transport implementation.

Retaining the local helper is the architecture for the current evidence. A shared
abstraction would create a new import and maintenance boundary without reducing
cross-module duplication. It could also invite unrelated controller or engine
tests to depend on UI-specific silent semantics. No shared fixture, global patch,
production import, or default-factory change is introduced.

### Current integration contract

The existing UI scenario constructs a controller and explicitly supplies the
silent transport factory. Each test receives an independent transport instance.
The transport must:

- accept the handshake target without opening a socket;
- accept text, binary, ping, close, and abort operations without external effects;
- expose an empty negotiated subprotocol;
- accept listener registration without emitting asynchronous callbacks; and
- preserve any existing test-visible target capture used to prove the connection
  path was entered.

These are test-support semantics, not a new production API. The UI test remains
responsible for driving the controller's opened or closed state and asserting
button, editor, and session-state outcomes.

### Future extraction shape and threshold

Extraction is permitted only after evidence records at least one additional
distinct relevant UI scenario or module that needs the same semantics, or
meaningful duplication that presents a realistic divergence risk. A test that
merely uses a transport double for engine-level frames, reconnect policy, or
network integration does not satisfy the threshold.

When the threshold is met, the future design is:

```text
UI scenario A ----\
                  +--> test-only silent transport support
UI scenario B ----/             |
                                | explicit factory injection
                                v
                  WebSocketSessionController
```

The support module should expose only the smallest transport-compatible factory
or constructor needed by the qualifying UI scenarios. It must remain under the
test support boundary, depend on the transport protocol types only, and never be
imported by production modules. Consumers must opt in explicitly so unrelated
tests keep their own purpose-specific doubles. Migration is complete only when
all qualifying scenarios preserve their observable state assertions and no live
network path is introduced.

### Ownership and dependency boundaries

| Component | Owns | Must not own or depend on |
| --- | --- | --- |
| UI lifecycle scenario | User-visible state assertions and event driving | Transport internals or live network access |
| Current local double | Hermetic no-op transport behavior for its module | Production code or unrelated test contracts |
| Session controller | Transport-factory injection and session lifecycle | Knowledge of a particular test double |
| Production transport | Real WebSocket I/O | Test-only helpers |
| Future shared support | Common behavior after the threshold is met | Global patching or broader transport policy |

### Compatibility, isolation, and failure behavior

- Production modules, transport defaults, protocol behavior, and user-facing
  behavior remain unchanged.
- Existing UI tests continue to use explicit, network-free injection and retain
  their current observable assertions.
- Per-test instances prevent state leakage between scenarios.
- The silent double does not synthesize callbacks, so event-driven state changes
  remain caused by the test's explicit controller actions.
- A future helper must preserve the same isolation and must not become a
  catch-all replacement for protocol-specific or integration doubles.

## Traceability

The following IDs are introduced for this architecture record and map directly to
the accepted requirements' user stories and Definition of Done.

| Requirement | Architectural response | Acceptance evidence |
| --- | --- | --- |
| R1: isolate UI lifecycle tests | Keep explicit silent transport injection | Focused existing UI lifecycle tests remain hermetic |
| R2: share only with demonstrated reuse | Use the distinct-consumer or drift-risk threshold | Consumer inventory and decision record are present |
| R3: preserve behavior when sharing | Future helper keeps the current protocol-compatible semantics | Existing qualifying scenarios retain state and isolation assertions |
| R4: retain local support when threshold is unmet | Select the current file-local helper | No shared test surface or code migration is planned |
| R5: change no production behavior | Keep all changes within task artifacts for this step | Production and protocol files remain unchanged |
| R6: preserve deterministic normal execution | No live network and no asynchronous callback emission | `make lint` and `make verify-ai-tasks` validate artifact integrity |
| R7: keep scope narrow and reversible | Revisit only on new consumer or meaningful duplication | Future trigger and migration boundary are documented |

| User story | Architectural response |
| --- | --- |
| Reliable UI lifecycle feedback | Hermetic, explicitly injected local transport |
| One source when multiple scenarios genuinely reuse behavior | Conditional test-only support module after threshold |
| Avoid unnecessary suite coupling | Retain local ownership while evidence shows one consumer boundary |

## Validation Strategy

For this architecture-only step, validation is limited to the requested Make
targets:

- `make lint` checks Markdown and repository lint rules.
- `make verify-ai-tasks` checks task-artifact integrity and roadmap consistency.

If the future threshold is met, the implementation step should add focused tests
for each qualifying UI scenario, run them through the repository's Make workflow,
and then run the normal quality gate. The migration must demonstrate unchanged
observable lifecycle behavior and absence of live network access before the
architecture decision is changed.

## Q&A

### Why not extract the helper now?

The inventory finds one consumer boundary: one UI lifecycle test module. Two
call sites in that module share one local owner, so extraction would add a suite
dependency without removing cross-module duplication.

### What event reopens this design?

A distinct relevant UI scenario or module that needs materially the same silent
transport behavior, or evidence that local duplication is likely to diverge,
reopens the decision. The new evidence must be recorded before extraction.

### Why are other transport doubles excluded?

They support different controller, session-engine, or integration contracts.
Consolidating them would broaden scope and could erase useful scenario-specific
behavior without satisfying the reuse requirement.
