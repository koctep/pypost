# PYPOST-462 — Developer Documentation

> Date: 2026-06-11
> Parent: [PYPOST-462](https://pypost.atlassian.net/browse/PYPOST-462)

---

## 1. What Changed and Why

PYPOST-462 is a **test-only** task. It adds end-to-end regression coverage for the
history-masking flow introduced by PYPOST-446. No production code or user-facing behavior
changed.

The new acceptance test in `tests/test_history_masking_e2e.py` verifies:

1. **Execute and persist** — `RequestService.execute` with hidden and non-hidden variables
   records a history entry with masked URL, headers, and body.
2. **Reload** — a fresh `HistoryManager` loads the persisted `history.json` (simulated app
   restart).
3. **History panel display** — `HistoryPanel` shows the reloaded entry; list label and detail
   widgets never contain the secret and preserve non-hidden values.

This closes the High-priority missing-test item from
[PYPOST-446 technical-debt analysis](ai-tasks/PYPOST-446/60-tech-debt.md).

---

## 2. Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/sensitive_data_masking_policy.md` | Added **Testing** section: unit/integration commands, new e2e test scope, run instructions, broader regression command. |
| `ai-tasks/PYPOST-446/70-dev-docs.md` | Updated **Testing** and **File Locations** to reference `tests/test_history_masking_e2e.py`; marked PYPOST-462 follow-up as done. |
| `doc/dev/README.md` | No change — navigation entry for sensitive data masking already present via PYPOST-446. |

No new `doc/dev/` file was required. PYPOST-446 STEP 7 already documents the masking policy;
PYPOST-462 extends the test reference so maintainers can find the connected-flow acceptance
check.

---

## 3. Running the New Test

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_history_masking_e2e.py -v
```

Broader history-masking regression:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_sensitive_data_masking_policy.py \
  tests/test_request_service.py \
  tests/test_history_masking_e2e.py -v
```

---

## 4. Test Design Notes

- Uses real `RequestService`, `HistoryManager`, `TemplateService`, and `HistoryPanel`; HTTP is
  mocked at the service boundary.
- Asserts both persisted entry fields and UI widget text after reload.
- Accesses private panel attributes (`_list_widget`, `_detail_*`) — same pattern as
  `tests/test_history_panel.py`.

---

## 5. Related Tickets

- [PYPOST-446](https://pypost.atlassian.net/browse/PYPOST-446) — hidden-variable masking in
  request history (parent feature).
- [PYPOST-462](https://pypost.atlassian.net/browse/PYPOST-462) — this task (integration test).
- [PYPOST-464](https://pypost.atlassian.net/browse/PYPOST-464) — masking metric empty vs
  non-empty hidden keys (separate scope).
- [PYPOST-463](https://pypost.atlassian.net/browse/PYPOST-463) — refactor history-recording
  block (separate scope).
