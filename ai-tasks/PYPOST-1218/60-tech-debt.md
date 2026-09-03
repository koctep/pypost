# PYPOST-1218 Technical Debt

The protocol remains exact-version rather than negotiated: clients and hosts
must upgrade together when version 2 is introduced. This is the intended
fail-closed behavior for the current local attach surface and is preferable to
binding an unknown client. Version negotiation, if needed, should be a new
protocol design rather than an implicit compatibility fallback.

No new Jira debt issue is required.
