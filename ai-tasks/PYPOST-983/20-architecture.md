# PYPOST-983: Centralize the forced-settle timeout contract

## Research

The accepted requirements and [Jira PYPOST-983](https://pypost.atlassian.net/browse/PYPOST-983)
identify three existing asynchronous UI timeout companions as the complete consumer set:

- `tests/test_agent_golden_e2e.py` passes a literal `0.05` to the forced text wait.
- `tests/test_agent_dialog_settle_e2e.py` owns a module-local `FORCED_SETTLE_TIMEOUT_S`.
- `tests/test_agent_e2e_http_mapping_multi_url.py` owns another module-local
  `FORCED_SETTLE_TIMEOUT_S`.

The existing helper boundaries are otherwise appropriate. `tests/helpers/agent_e2e_send.py`
owns the normal `SEND_SETTLE_TIMEOUT_S` budget (`15.0` seconds),
`tests/helpers/agent_e2e_send_settle.py` owns response-settle mechanics, and
`tests/helpers/agent_e2e_dialog_settle.py` owns modal-settle mechanics. None of those
mechanics should absorb the forced budget because the policy is shared across text,
snapshot, and modal waits.

## Implementation Plan

1. Add `tests/helpers/agent_e2e_timeouts.py` as the test-harness policy module. It will
   export exactly one shared `FORCED_SETTLE_TIMEOUT_S = 0.05` contract and no waiting,
   diagnostic, or UI behavior.
2. Replace the golden literal and the dialog and mapping module-local definitions with
   direct imports from `tests.helpers.agent_e2e_timeouts`. Keep every existing wait call,
   message, condition name, step identifier, and diagnostic assertion otherwise unchanged.
3. Leave `SEND_SETTLE_TIMEOUT_S`, the dialog's normal `DIALOG_SETTLE_TIMEOUT_S`, and all
   helper implementations independent. This preserves the distinction between a forced
   failure probe and a normal asynchronous settle.
4. Validate the three named companions through the repository's Make-based focused test
   path, then run `make lint`, `make verify-ai-tasks`, and the relevant broader Make quality
   gate. Confirm that only the new policy helper, three consumer imports, and task artifacts
   are in scope.

**Mandatory — Failing Repro (next Step 3):** N/A — no behavioral change. This is a
test-harness ownership change that preserves the same numeric timeout and all existing
wait and diagnostic behavior. Step 3 should record the N/A rationale rather than adding a
red runtime test or changing the existing companion assertions.

## Architecture

### Components and ownership

`tests/helpers/agent_e2e_timeouts.py` is the single owner of the forced-settle policy. Its
small public interface is:

```python
FORCED_SETTLE_TIMEOUT_S = 0.05
```

The three scenario modules are consumers only:

| Consumer | Existing wait mechanism | Use of shared contract |
| --- | --- | --- |
| `test_agent_golden_e2e.py` | `AgentAppSession.wait_for_text` | Import for the forced status wait |
| `test_agent_dialog_settle_e2e.py` | `run_product_dialog_settle` | Import for the forced modal wait |
| `test_agent_e2e_http_mapping_multi_url.py` | `wait_response_after_snapshot` | Import for the forced mapping wait |

The policy module has no application imports and no dependency on any consumer. It is
deliberately separate from `agent_e2e_send.py`: the latter's `SEND_SETTLE_TIMEOUT_S` remains
the owner of the normal Send budget, while the new module owns only the near-zero forced
budget. No package re-export or `tests/helpers/__init__.py` change is needed; direct imports
make each consumer's dependency discoverable at its use site.

### Interaction scheme

```text
                    +--------------------------------------+
                    | tests/helpers/agent_e2e_timeouts.py  |
                    | FORCED_SETTLE_TIMEOUT_S = 0.05       |
                    +------------------+-------------------+
                                       |
                    +------------------+-------------------+
                    |                  |                   |
                    v                  v                   v
          golden text wait    dialog modal wait    mapping snapshot wait
          (scenario wrapper)  (settle helper)       (response helper)

  Normal budgets remain separate:
  agent_e2e_send.py -> SEND_SETTLE_TIMEOUT_S -> response settle defaults
  dialog test module -> DIALOG_SETTLE_TIMEOUT_S -> successful modal settle
```

The shared module supplies a value only. Each consumer retains responsibility for its own
scenario setup, asynchronous wait primitive, failure message, diagnostic enrichment, and
assertions. Consequently, the golden response excerpt, dialog modal scalars, mapping
response excerpt, and their existing `step` and condition identities remain unchanged.

### Pattern and invariants

The selected pattern is a single-source-of-truth test policy constant. It is the smallest
safe structure for preventing drift without introducing a generic timeout abstraction or
coupling unrelated helpers. The implementation must preserve these invariants:

- the value remains exactly `0.05` seconds;
- all three named forced companions import the same symbol;
- no named companion retains an independent forced-timeout value;
- normal settle budgets and their defaults are unchanged;
- timeout calls remain bounded by the existing session/helper mechanisms;
- scenario-specific messages, condition names, step identifiers, diagnostic fields, and
  assertions remain semantically and textually stable unless an import-only edit requires
  adjacent formatting; and
- test module names, test function names, markers, and pytest discoverability are unchanged.

### Validation and traceability

The development step should verify the new helper's exact value and all three consumer
imports through focused Make-based tests or the repository's existing companion coverage.
It should also inspect the source to ensure no second forced-timeout definition remains in
the named modules. `make lint` checks Python style and `make verify-ai-tasks` checks the
workflow artifacts; the broader Make quality gate provides regression coverage. Protected
baseline files, `AGENTS.md`, the sprint registry, and unrelated tests must remain untouched.

| Requirement | Architectural guarantee |
| --- | --- |
| One authoritative 0.05-second contract | Dedicated helper owns the sole constant |
| All three companions use it | Direct imports at each consumer boundary |
| Diagnostics and scenario identity preserved | Wait mechanics and arguments remain local |
| Normal settle remains distinct | Existing normal-budget owners are not changed |
| Bounded, discoverable tests | Existing wait primitives, markers, and test names remain |
| No unrelated behavior changes | Test-only helper and import edits; no production dependency |

## Q&A

**Why is a new helper module preferable to `agent_e2e_send.py`?**

The forced policy is shared by a golden text wait, a dialog modal wait, and a mapping
snapshot wait. Giving it a neutral timeout-policy owner avoids implying that it belongs to
the normal Send budget or to one particular wait primitive.

**Should the helper wrap or configure the wait functions?**

No. Wrapping them would risk changing exception construction, diagnostic fields, or modal
cleanup. The helper exports only the value; existing scenario-specific mechanics stay in
place.

**Does Step 3 need a red test?**

No. The requested change has no runtime behavior to reproduce: the pre- and post-change
forced waits both receive `0.05`. Existing focused tests validate that the consumers still
exercise their current failure paths.

**What is explicitly out of scope?**

Production code, user-facing behavior, normal settle budgets, unrelated timeout constants,
new scenarios, diagnostic formats, and broad timeout refactors are all excluded.
