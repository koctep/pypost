# PYPOST-836: Technical Debt Analysis

## Shortcuts Taken

- **Fill via setters, not keystrokes** — `ui_fill` uses `clear` + `setText` /
  `setPlainText` for deterministic offscreen CI. Character-by-character typing is
  not simulated; `ui_send_key` covers real key delivery for keys/hotkeys.
- **Select is combo-box only** — `ui_select` targets `QComboBox` by display text.
  Tree/list selection is deferred until a golden-flow or product need requires it.
- **Session helpers use window root** — `AgentAppSession.ui_*` looks up under
  `MainWindow`. Multi-tab per-role ids still require a scoped root via the module
  API (same rule as `ui_identity.md`).

## Code Quality Issues

- Key name resolution is a small alias map + `Qt.Key` getattr; exotic keys need
  explicit aliases if agents start depending on them.
- No shared “current tab” helper for scoped lookup; callers compose
  `find_widget(tab, id)` themselves.

## Missing Tests

- No multi-tab regression that proves window-root `findChild` hits the wrong tab
  (documented risk; golden flow / settle stories may own it).
- Hotkey assertion is smoke-only (Ctrl+A must not raise), not a full select-all
  behavioral check under every platform plugin.
- No explicit `caplog` assertion for `ui_action_applied` (optional hardening).

## Performance Concerns

None material. Actions are O(tree) `findChild` plus one Qt input event; suitable
for harness use. High-frequency polling should still prefer snapshot + settle
waits (837) rather than spamming clicks.

## Follow-up Tasks

Jira: [PYPOST-851](https://pypost.atlassian.net/browse/PYPOST-851)

1. **Scoped current-tab lookup helper** — Optional `AgentAppSession` helper that
   resolves per-tab ids against the active request tab to reduce caller mistakes.
2. **Broader select targets** — Extend `ui_select` (or a sibling) for list/tree
   selection when golden-flow needs it.
3. **Optional fill-via-keyClicks mode** — If agents need keystroke-level realism
   (IME, validation-on-key), add an opt-in path without breaking deterministic fill.
4. **caplog contract for `ui_action_applied`** — Assert DEBUG scalars and absence
   of fill text in logs (align with snapshot logging tests if added).
5. **Out-of-process MCP wrapper** — Packaging story may expose these primitives
   over a local agent/MCP bridge; keep `MCPServerImpl` HTTP tools separate.
