# PYPOST-1218 Observability

Rejected handshakes emit:

`agent_ui_attach_handshake_rejected endpoint=<path> version=<value>
expected_version=1`

The event is WARNING-level and records only endpoint/version metadata. A
successful version-1 handshake continues to emit
`agent_ui_attach_handshake_ok`. No UI action or payload is processed before a
handshake is accepted.
