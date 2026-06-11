# PYPOST-332 — Developer Documentation

> Date: 2026-06-11
> Parent: PYPOST-35 / PYPOST-328

---

## 1. What Changed and Why

PYPOST-332 adds automated test coverage for open-tab closure when collection tree items are
deleted. Production behavior was implemented in PYPOST-328; this task ensures regressions are
caught in CI.

---

## 2. Test Files

| File | Coverage |
| --- | --- |
| `tests/test_tabs_presenter.py` | `close_tabs_for_request_ids` unit behavior |
| `tests/test_collections_presenter.py` | `requests_deleted` signal emission |
| `tests/test_delete_open_tabs_integration.py` | Presenter signal wiring (mirrors `MainWindow`) |

---

## 3. Documentation Updated

- `doc/dev/collection_item_delete.md` — added **Testing** section with focused commands.

---

## 4. Testing

Focused suites:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_tabs_presenter.py \
  tests/test_collections_presenter.py \
  tests/test_delete_open_tabs_integration.py -k "close_tabs or requests_deleted or DeleteOpenTabs"
```

Full regression:

```bash
make test
```

---

## 5. Related Tickets

- `PYPOST-35` — collection item delete feature.
- `PYPOST-328` — close tabs on delete implementation.
- `PYPOST-332` — open-tab delete tests (this task).
