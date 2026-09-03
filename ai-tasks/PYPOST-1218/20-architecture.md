# PYPOST-1218 Architecture

## Handshake boundary

```text
AF_UNIX client ── handshake {op, version} ──> AgentUiAttachHost
                                                   │
                                  version == 1? ───┴── yes → bind / serve UI ops
                                                   └── no  → reject / close peer
```

`AgentUiAttachHost._handle_request` validates the version before entering the
existing UI dispatch path. The reply includes `ok: false`, an operator-safe
version error, and the host's expected version. The sidecar already treats a
false handshake reply as `AttachUnboundError`, so no client-side protocol
change is required.

## Compatibility

The current `ATTACH_PROTOCOL_VERSION` remains `1`; successful clients see no
behavior change. The check is exact, so a missing field, a different integer,
or a value of another type fails closed. No version negotiation is attempted.
