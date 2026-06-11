# PYPOST-352: Close debt — ResponseView search GUI tests in headless CI

## Goals

Original PYPOST-37 debt recorded that ResponseView search lacked automated GUI tests because
headless CI crashed. Subsequent work (PYPOST-365, PYPOST-357) added Qt-level tests using the
project `qapp` fixture and offscreen platform. This task closes the debt by verifying coverage
and documenting the headless test path.

## Definition of Done

1. Automated GUI tests exist for ResponseView search behavior.
2. Tests pass locally with `QT_QPA_PLATFORM=offscreen` (same as CI/Makefile).
3. Debt item PYPOST-352 is traceable to test files and dev docs.

## Task Description

Verification-only closure. No new product behavior.
