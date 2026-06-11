# PYPOST-514 — Developer Documentation

> Team Lead: team_lead
> Date: 2026-06-11
> Sprint: Request Body Editor

---

## 1. What Changed and Why

PYPOST-514 adds an optional **YAML as JSON** checkbox on the Body tab. Users can keep authoring
request bodies in YAML while sending JSON to APIs that require `application/json`. Conversion runs
at send time in the HTTP client; the editor text remains YAML. Invalid YAML fails closed with a
dedicated `ErrorCategory.BODY` message instead of sending a misleading payload.

---

## 2. New and Updated Modules

- `pypost/core/yaml_json_converter.py` (new)
  - `YamlBodyConversionError` — typed conversion failure.
  - `convert_yaml_body_to_object()` — `safe_load_all`, single-document enforcement,
    `json.dumps` serializability check.
- `pypost/models/models.py`
  - `RequestData.yaml_as_json: bool = False`.
- `pypost/models/errors.py`
  - `ErrorCategory.BODY`.
- `pypost/core/http_client.py`
  - YAML + flag branch in `_prepare_request_kwargs`; ERR log on failure.
- `pypost/core/request_service.py`
  - BODY errors non-retryable in `_execute_http_with_retry`.
- `pypost/ui/presenters/tabs_presenter.py`
  - `_ERROR_MESSAGES[ErrorCategory.BODY]`.
- `pypost/ui/widgets/request_editor.py`
  - `yaml_as_json_check` on format row; enable only for YAML format; load/save persistence.
- `requirements.txt`
  - `PyYAML` dependency.

---

## 3. Documentation Updated

- `doc/dev/yaml_as_json.md` (new)
  - Overview, architecture diagram, send-time flow, API/usage, configuration, observability,
    troubleshooting, test references, related tickets.
- `doc/dev/body_format_selector.md`
  - Cross-reference to YAML-as-JSON send conversion.
- `doc/dev/README.md`
  - Table of contents entry for PYPOST-514.

---

## 4. Configuration Summary

| Item | Value |
| --- | --- |
| Model field | `RequestData.yaml_as_json` (default `False`) |
| Dependency | `PyYAML` (`yaml.safe_load_all`) |
| Env vars / settings | None |
| Metrics | None (per architecture decision) |

---

## 5. Testing

Focused suites:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_yaml_json_converter.py \
  tests/test_http_client.py \
  tests/test_request_editor_body_format.py \
  tests/test_retry.py -k body
```

---

## 6. Related Tickets

- `PYPOST-513` — Body format selector.
- `PYPOST-514` — YAML-as-JSON send conversion (this task).
- `PYPOST-515` — Paste-time JSON→YAML when checkbox is on (follow-up).
