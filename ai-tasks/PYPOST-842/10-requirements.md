# PYPOST-842: Assert metrics port free after shutdown

## Goals

Smoke must fail if an agent session leaves its ephemeral metrics port bound
after shutdown, so CI catches listener leaks instead of only soft-relaunching.

## Programming Language

Python

## User Stories

- As a **maintainer**, I want a socket-level assert after shutdown so FR6 is hard.

## Definition of Done

- Smoke asserts the first session’s metrics port is free after shutdown.
- Docs mention the hard FR6 check.

## Task Description

Strengthen soft relaunch coverage with a bind check on the prior metrics port.

## Q&A

| Question | Answer |
| --- | --- |
| Already free today? | Yes after PYPOST-841 / existing stop_server — this locks it. |
