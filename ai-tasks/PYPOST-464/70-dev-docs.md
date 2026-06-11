# PYPOST-464 — Developer Documentation

> Date: 2026-06-11
> Parent: [PYPOST-464](https://pypost.atlassian.net/browse/PYPOST-464)

---

## 1. What Changed and Why

PYPOST-464 is a **test-only** task. It adds Prometheus registry scrape tests for the
`hidden_value_masks_applied_total` counter introduced by PYPOST-446. No production code or
user-facing behavior changed.

The new tests in `tests/test_history_masking_metrics.py` verify:

1. **Empty hidden keys** — counter line is absent from scrape output when `hidden_keys` is `set()`
   or `None`.
2. **Non-empty hidden keys** — counter equals `1.0` for `surface="history"` after history write.

This closes the Normal/Medium missing-test item from
[PYPOST-446 technical-debt analysis](ai-tasks/PYPOST-446/60-tech-debt.md).

---

## 2. Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/sensitive_data_masking_policy.md` | Added **Metric counter tests (PYPOST-464)** section with run commands and test scope. |
| `ai-tasks/PYPOST-446/70-dev-docs.md` | Updated **Testing** and **File Locations** to reference `tests/test_history_masking_metrics.py`. |

No new `doc/dev/` file was required.

---

## 3. Running the New Tests

```bash
.venv/bin/python -m pytest tests/test_history_masking_metrics.py -v
```

Broader history-masking regression (includes mock unit tests and e2e):

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_sensitive_data_masking_policy.py \
  tests/test_request_service.py \
  tests/test_history_masking_metrics.py \
  tests/test_history_masking_e2e.py -v
```

---

## 4. Relationship to Existing Tests

| File | Role |
| --- | --- |
| `tests/test_request_service.py` | Fast mock-based checks that `track_hidden_value_mask_applied` is called |
| `tests/test_history_masking_metrics.py` | Registry scrape checks for real counter values (PYPOST-464) |
| `tests/test_history_masking_e2e.py` | Persistence/reload/UI journey (PYPOST-462) |

All three layers are complementary; none replaces the others.
