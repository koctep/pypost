# PYPOST-844: Assert theme apply keeps objectNames

## Goals

Theme / `apply_settings` must leave key automation identities intact so agents
do not lose widget lookup after appearance changes.

## Programming Language

Python

## Definition of Done

- Automated assert that applying a theme via `apply_settings` preserves key
  `objectName`s (and accessibleIdentifier mirrors).
- Spot-check / ui_identity docs mention the lock.

## Task Description

Optional follow-up from PYPOST-834: construction-only setters make loss low
risk; lock it in CI.

## Q&A

| Question | Answer |
| --- | --- |
| Production change needed? | No if behavior already holds — deliver the lock test. |
