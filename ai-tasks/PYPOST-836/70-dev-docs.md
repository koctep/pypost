# PYPOST-836: Dev Docs Report

## Documentation created / updated

- [x] `doc/dev/ui_actions.md` — overview, architecture, API, errors, session
  helpers, scoped lookup, troubleshooting
- [x] `doc/dev/README.md` — TOC link under Testing and quality
- [x] `doc/dev/agent_lifecycle.md` — actions in API table; DEBUG event; smoke
  note; Related link; siblings list updated
- [x] `doc/dev/ui_identity.md` — Related link to actions
- [x] `doc/dev/ui_snapshot.md` — Related link to actions
- [x] `doc/dev/gui_testing.md` — actions link after snapshot section
- [x] `doc/dev/logging.md` — catalog `ui_action_applied` (DEBUG fields)

## Template coverage

- [x] Overview
- [x] Architecture
- [x] API / Usage (`ui_click`, `ui_fill`, `ui_select`, `ui_send_key`, session)
- [x] Configuration (none; identity + ready preconditions)
- [x] Troubleshooting

## Validation

- [x] Docs match public signatures and exception types
- [x] Identity-first addressing and multi-tab scoping documented
- [x] DEBUG `ui_action_applied` fields: `primitive`, `widget_id`, `outcome`,
  `duration_ms` — no fill text / option / key payloads
- [x] Cross-links to lifecycle, identity, snapshot, GUI testing, logging present
