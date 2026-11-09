# PYPOST-1532: Technical Debt Analysis

## Shortcuts Taken

None. This task made no production or test change. The accepted decision keeps
the existing hard 100 ms cutoff. No temporary budget, soft mark, or
benchmark-only timer was introduced.

## Code Quality Issues

None. `HiddenFieldsTable`, `HiddenFieldsTableModel`, and
`tests/test_hidden_fields_virtualization_repro.py` stay as delivered. The
solution matches the architecture. Structural guards and `elapsed < 0.1`
remain hard assertions. The literals `1000` and `0.1` are the accepted list
size and cutoff.

## Missing Tests

None. No behavioral change required a new test. The existing large-list check
already covers virtualization, a row count of 1,001, the lightweight `item()`
facade, selector text, and the 100 ms cutoff.

No timeout BLOCKER. The module already declares
`pytestmark = pytest.mark.timeout(30)` in
`tests/test_hidden_fields_virtualization_repro.py`, so every test in that
file has an explicit timeout marker.

## Performance Concerns

The residual CI risk remains. A healthy load of 1,000 selectors can still miss
the hard `elapsed < 0.1` cutoff when a shared runner is busy, while the table
stays a lightweight virtualized list. The recorded environment risk is not an
observed flake of this check. The hard cutoff stays. This residual risk is
accepted by this decision and is not a new ticket.

Scroll-frame rate and process-memory measurement stay outside this task. No
new performance work was added.

## Follow-up Tasks

None.

The residual CI risk of the hard 100 ms cutoff is accepted by this decision
and is not a new ticket. Opening one would duplicate PYPOST-1532. A later
change waits for an observed flake of this check. This step records no
pre-existing test failure.
