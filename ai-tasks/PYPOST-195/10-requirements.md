# PYPOST-195: Close debt — stream size estimation via UTF-8 length

## Goals

Close follow-up debt from [PYPOST-26](https://pypost.atlassian.net/browse/PYPOST-26): document
and accept streaming response size estimation approach.

## Definition of Done

- [x] Size metric derived from UTF-8 encoded length of received text
- [x] Wire-byte divergence acknowledged as acceptable for text/SSE scope

## Task Description

Sprint 492 debt closure. Accurate wire-byte accounting deferred unless binary streaming becomes
a requirement.
