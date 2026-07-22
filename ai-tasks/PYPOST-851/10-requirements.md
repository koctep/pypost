# PYPOST-851: Agent UI actions follow-ups

## Goals

Reduce multi-tab lookup mistakes and harden action logging for agents.

## Programming Language

Python

## Definition of Done

- Session can scope actions to the current request tab.
- Caplog asserts `ui_action_applied` scalars and no fill body in logs.
- Remaining optional items (broader select, keyClicks fill, MCP packaging)
  documented as deferred debt.

## Task Description

Bundle of PYPOST-836 follow-ups; deliver scoped lookup + logging lock first.
