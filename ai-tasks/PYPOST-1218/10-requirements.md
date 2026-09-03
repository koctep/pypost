# PYPOST-1218 Requirements

## Business reason

The agent-UI attach handshake currently accepts any client-declared protocol
version. A future wire revision could bind successfully and then mis-dispatch
operations instead of failing before attachment.

## Functional requirements

1. Require the client handshake version to equal `ATTACH_PROTOCOL_VERSION`.
2. Reject missing, non-integer, and unsupported versions before any UI action
   can be dispatched.
3. Return a clear failure reply that the existing attach client maps to
   `AttachUnboundError`.
4. Preserve the successful version-1 handshake and all existing UI actions.
5. Add automated coverage for a mismatched version.
6. Update the attach verification and logging documentation.

## Non-functional requirements

- Validation must be local and deterministic; no new network or dependency is
  introduced.
- Rejection must not disclose UI state or payload data.
- Existing Make-driven attach, sidecar, and product MCP tests remain green.

## Out of scope

- Protocol negotiation or support for multiple versions simultaneously.
- Changes to the AF_UNIX framing or UI action semantics.

## Acceptance criteria

- An exact version-1 handshake returns `ok: true`.
- Any other version returns `ok: false` and does not bind the client.
- A focused automated test proves mismatch rejection.
