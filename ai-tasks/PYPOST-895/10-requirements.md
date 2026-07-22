# PYPOST-895 Requirements

Share Send settle timeout constant across agent e2e Send scenarios.

## Acceptance

- [x] `tests/helpers/agent_e2e_send.py` exports `SEND_SETTLE_TIMEOUT_S = 15.0`
- [x] Golden, matrix, double-body, env, seed POST import the shared constant
