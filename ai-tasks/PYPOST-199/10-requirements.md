# PYPOST-199: Close debt — full body accumulation on streams

## Goals

Close follow-up debt from [PYPOST-26](https://pypost.atlassian.net/browse/PYPOST-26): decide
memory strategy for streaming response bodies.

## Definition of Done

- [x] Full body accumulation in `HTTPClient` and UI accepted for current scope
- [x] Tail buffer / bounded retention deferred to PYPOST-201

## Task Description

Sprint 492 debt closure. Infinite streams may grow memory; tail mode is a separate follow-up.
