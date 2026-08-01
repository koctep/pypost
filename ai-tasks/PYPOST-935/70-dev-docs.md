# PYPOST-935 Dev Docs

Developer documentation updated in Step 4; verified in Step 8.

## Updated files

| File | Change |
| --- | --- |
| `doc/dev/ui_identity.md` | Catalog row for `SETTINGS_DIALOG` (`pypost_settings_dialog`); noted modal / not in `KEY_WIDGET_IDS` |
| `doc/dev/agent_dialog_settle.md` | Presence signal uses `objectName == SETTINGS_DIALOG`; `_modal_diag()` documents `dialog_object_name`; troubleshooting row for identity-based settle |

## Index / cross-links

- `doc/dev/README.md` — already indexes `ui_identity.md` and
  `agent_dialog_settle.md` (no change required).

## Overview

`SettingsDialog` now exposes stable widget identity for agents and tests.
Dialog-settle coverage recognizes the modal by `objectName` instead of window
title + Python type.
