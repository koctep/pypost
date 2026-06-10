# PYPOST-490 — Developer Documentation

> Date: 2026-06-11
> Parent: [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490)

---

## 1. What Changed and Why

PYPOST-490 is a **test-only** task. It adds end-to-end regression coverage for the
settings-to-toggle-log flow introduced by PYPOST-448. No production code or user-facing
behavior changed.

The new acceptance tests in `tests/test_settings_hidden_toggle_logging_e2e.py` verify:

1. **Default policy** — after `SettingsDialog` save and `MainWindow.apply_settings`, opening
   the environment manager and toggling hidden emits `key=********` (no readable key name).
2. **Opt-in policy** — with `log_hidden_key_names=True`, the same journey emits the readable
   variable key name.
3. **Privacy** — in both modes, logs include `env_name` and `hidden`, and never include
   variable values.

This closes the High-priority missing-test item from
[PYPOST-448 technical-debt analysis](ai-tasks/PYPOST-448/60-tech-debt.md).

---

## 2. Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/hidden_variables.md` | Added `tests/test_settings_hidden_toggle_logging_e2e.py` to **Related Tests** with a short scope note (PYPOST-490 end-to-end journey). |
| `doc/dev/README.md` | No change — navigation entry for hidden variables already present. |

No new `doc/dev/` file was required. PYPOST-448 STEP 7 already documents the feature
(overview, architecture, configuration, troubleshooting). PYPOST-490 only extends the test
reference list so maintainers can find the connected-flow acceptance check.

---

## 3. Running the New Tests

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_settings_hidden_toggle_logging_e2e.py -v
```

Broader hidden-toggle / settings regression:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_hidden_toggle_log_policy.py \
  tests/test_env_dialog.py \
  tests/test_settings_dialog.py \
  tests/test_settings_persistence.py \
  tests/test_settings_hidden_toggle_logging_e2e.py -v
```

---

## 4. Related Tickets

- [PYPOST-448](https://pypost.atlassian.net/browse/PYPOST-448) — configurable hidden-key
  toggle logging (parent feature).
- [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490) — this task (integration test).
- [PYPOST-489](https://pypost.atlassian.net/browse/PYPOST-489) — separate persistence
  round-trip e2e with default masked logging (not covered here).

---

## 5. Review

STEP 7 awaits user approval before marking complete in `00-roadmap.md`.
