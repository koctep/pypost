# PYPOST-960: Observability

No logging or metric changes. Existing events unchanged:

| Event | Level | When |
| --- | --- | --- |
| `agent_e2e_failure_artifacts_failed` | WARNING | Dump helper catches `DUMP_BEST_EFFORT_ERRORS` |
| `agent_session_failure_dump_hook_failed` | WARNING | Hook wrapper catches `DUMP_BEST_EFFORT_ERRORS` |

Same exception types → same WARNING paths as before PYPOST-960.
