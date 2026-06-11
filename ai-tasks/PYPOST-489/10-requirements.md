# PYPOST-489: Extend env persistence e2e for default masked toggle logging

## Goals

PYPOST-448 made hidden-flag toggle logs respect a logging policy: by default, variable key
names must not appear in readable form. PYPOST-490 covers the settings → apply → environment
manager journey. This task closes the remaining gap: **storage round-trip** scenarios where
`EnvironmentDialog` is constructed without an explicit `log_hidden_key_names` argument must
still emit masked key names in toggle logs.

## Programming Language

Python 3.10+

## User Stories

- As a **security-conscious user**, I want assurance that default masked logging still holds
  after environments are saved and reloaded, so persistence does not weaken privacy.
- As a **maintainer**, I want an acceptance check in `test_env_persistence_e2e.py` traceable to
  PYPOST-448 debt, so regressions in default constructor behavior are caught.

## Definition of Done

1. An automated test in `tests/test_env_persistence_e2e.py` saves an environment, reloads it
   from storage, opens `EnvironmentDialog` **without** `log_hidden_key_names`, toggles a
   hidden flag, and asserts the toggle log uses masked key names.
2. The test confirms `env_name` and `hidden` appear in the log; variable key and value do not
   appear in readable form.
3. No product behavior change unless a defect is found; deliverable is test coverage.
4. Traceable to [PYPOST-448 technical-debt analysis](ai-tasks/PYPOST-448/60-tech-debt.md) and
   Jira [PYPOST-489](https://pypost.atlassian.net/browse/PYPOST-489).

## Out of Scope

- Settings → apply → presenter chain (PYPOST-490).
- Opt-in readable key-name logging mode.
- Production code changes unless a wiring defect is discovered.

## Q&A

| Question | Answer |
| --- | --- |
| Boundary with PYPOST-490? | PYPOST-490 owns settings wiring; PYPOST-489 owns persistence round-trip with default dialog constructor. |
| Should values appear in logs? | No — inherited from PYPOST-437 / PYPOST-448. |
