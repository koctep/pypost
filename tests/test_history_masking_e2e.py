"""PYPOST-462: integration test for hidden-value masking across save/reload history flow."""


import pytest

pytestmark = pytest.mark.timeout(120)

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from pypost.core.http_client import HTTPRequestResult, ResolvedRequestFields
from pypost.core.history_manager import HistoryManager
from pypost.core.request_service import RequestService
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.ui.widgets.history_panel import HistoryPanel

HIDDEN_KEY = "token"
HIDDEN_VALUE = "supersecret"
VISIBLE_KEY = "host"
VISIBLE_VALUE = "myserver.com"


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _make_response(status=200, body="OK"):
    return ResponseData(
        status_code=status, headers={}, body=body, elapsed_time=0.1, size=len(body)
    )


def _make_request() -> RequestData:
    return RequestData(
        method="POST",
        url="http://{{host}}/api?token={{token}}",
        headers={"Authorization": "Bearer {{token}}"},
        body='{"token":"{{token}}","host":"{{host}}"}',
        post_script="",
    )


def _history_manager_at(history_path: Path) -> HistoryManager:
    return HistoryManager(history_path=history_path)


def _execute_and_persist(history_path: Path) -> None:
    hm = _history_manager_at(history_path)
    svc = RequestService(history_manager=hm, template_service=TemplateService())
    svc.http_client = MagicMock()
    svc.http_client.send_request.return_value = HTTPRequestResult(
        response=_make_response(200),
        resolved=ResolvedRequestFields(
            url=f"http://{VISIBLE_VALUE}/api?token={HIDDEN_VALUE}",
            headers={"Authorization": f"Bearer {HIDDEN_VALUE}"},
            body=f'{{"token":"{HIDDEN_VALUE}","host":"{VISIBLE_VALUE}"}}',
        ),
    )
    svc.execute(
        _make_request(),
        variables={HIDDEN_KEY: HIDDEN_VALUE, VISIBLE_KEY: VISIBLE_VALUE},
        hidden_keys={HIDDEN_KEY},
    )
    hm.flush()


def _reloaded_panel(history_path: Path) -> HistoryPanel:
    hm = _history_manager_at(history_path)
    panel = HistoryPanel(history_manager=hm)
    panel._list_widget.setCurrentRow(0)
    return panel


def _assert_no_secret_leak(text: str) -> None:
    assert HIDDEN_VALUE not in text


def test_hidden_values_stay_masked_after_history_reload_in_panel(qapp):  # noqa: ARG001
    with tempfile.TemporaryDirectory() as td:
        history_path = Path(td) / "history.json"

        # Journey step 1–3: execute request, mask hidden values, persist history.
        _execute_and_persist(history_path)

        # Journey step 4–5: reload persisted history (simulated app restart).
        hm = _history_manager_at(history_path)
        entries = hm.get_entries()
        assert len(entries) == 1
        entry = entries[0]
        assert entry.url == "http://myserver.com/api?token=***"
        assert entry.headers["Authorization"] == "Bearer ***"
        assert entry.body == '{"token":"***","host":"myserver.com"}'

        # Journey step 6: History panel displays reloaded entry.
        panel = _reloaded_panel(history_path)

        assert panel._list_widget.count() == 1
        list_label = panel._list_widget.item(0).text()
        _assert_no_secret_leak(list_label)
        assert "http://myserver.com/api?token=***" in list_label

        url_text = panel._detail_url.text()
        headers_text = panel._detail_headers.toPlainText()
        body_text = panel._detail_body.toPlainText()

        _assert_no_secret_leak(url_text)
        _assert_no_secret_leak(headers_text)
        _assert_no_secret_leak(body_text)

        assert url_text == "http://myserver.com/api?token=***"
        assert VISIBLE_VALUE in url_text
        assert "Bearer ***" in headers_text
        assert body_text == '{"token":"***","host":"myserver.com"}'
        assert VISIBLE_VALUE in body_text
