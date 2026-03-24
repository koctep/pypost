# PYPOST-53: Environment context menu — duplicate environment

## Goals

Users need a quick way to create a new environment that matches an existing one (same
variables and MCP setting) under a new name, without retyping values. The Manage
Environments dialog should expose this from the environment list via a context menu.

## User Stories

- As a user, I want to open a context menu on an environment in Manage Environments
  and choose **Copy** so that I get a new environment duplicated from the selected one.
- As a user, I want to name the duplicate (with a sensible default) so I can tell it
  apart from the original.
- As a user, I want the app to reject a duplicate name that already exists so my
  environments are not overwritten by mistake.

## Definition of Done

- Context menu is available on the environment list inside Manage Environments.
- The menu includes **Copy**, which creates a **new** environment; the source is
  unchanged.
- The new environment has the same variable key/value pairs and the same **Enable MCP**
  flag as the source.
- The user is prompted for the new name; the suggested default is `Copy of <source name>`.
- If the entered name is empty or already used by another environment, the user is
  informed and can correct it; no silent overwrite.
- After success, the new environment appears in the list and can be edited on its own.

## Task Description

Today, Manage Environments supports adding and deleting environments and editing
variables per environment. There is no way to clone an environment. This task adds
**Copy** on the environment list’s context menu to mean **duplicate environment**
(not copying the name to the system clipboard). The implementation language for
pypost is **Python**.

## Q&A

- **Q:** What does **Copy** mean here?  
  **A:** Duplicate the environment (new entry, copied variables and MCP flag), not
  clipboard copy of the name. Jira description was aligned with this behaviour.

- **Q:** Is the toolbar environment selector in scope?  
  **A:** No; only the Manage Environments dialog list.
