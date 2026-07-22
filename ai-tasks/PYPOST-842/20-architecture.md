# PYPOST-842: Architecture

Expose `AgentAppSession.metrics_port` (port chosen in `start`) and assert
`bind(127.0.0.1, port)` succeeds after context exit in relaunch smoke.

**Step 3 N/A** — production already frees the port; deliverable is the lock.
