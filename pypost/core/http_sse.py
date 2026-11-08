"""SSE response handling helpers for HTTP transport."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from pypost.models.models import RequestData
from pypost.models.response import ResponseData

SSE_PROBE_TIMEOUT = 10.0
SSE_PROBE_CONNECT_TIMEOUT = 3.0
SSE_PROBE_MAX_EVENTS = 5


def _is_sse_content_type(content_type: str) -> bool:
    """Return True when Content-Type indicates an SSE response body."""
    if not content_type:
        return False
    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type == "text/event-stream"


def _headers_accept_event_stream(headers: Dict[str, str]) -> bool:
    """Return True when the request Accept header asks for event-stream."""
    accept = headers.get("Accept", "")
    return "text/event-stream" in accept.lower()


def handle_sse_response(
    response: Any,
    request_data: RequestData,
    start_time: float,
) -> ResponseData:
    """Process an SSE response probe and return a ResponseData summary."""
    import sseclient

    elapsed = time.time() - start_time
    resp_headers = dict(response.headers)

    if response.status_code != 200:
        try:
            body = response.text
        except Exception:
            body = f"HTTP {response.status_code}"
        response.close()
        return ResponseData(
            status_code=response.status_code,
            headers=resp_headers,
            body=body,
            elapsed_time=elapsed,
            size=len(body.encode("utf-8")),
        )

    events: List[str] = []
    try:
        client = sseclient.SSEClient(response)
        for i, event in enumerate(client.events()):
            if i >= SSE_PROBE_MAX_EVENTS:
                break
            desc = event.event or "message"
            if event.data:
                data = event.data or ""
                desc += f": {data[:100]}..." if len(data) > 100 else f": {data}"
            events.append(desc)
    except Exception as e:
        response.close()
        err_str = str(e)
        if "timed out" in err_str or "ReadTimeout" in type(e).__name__:
            body = (
                "SSE stream opened. Connection established. "
                "Server may not send events until client sends InitializeRequest."
            )
        else:
            body = f"SSE probe: connection opened, parse error: {e}"
        return ResponseData(
            status_code=200,
            headers=resp_headers,
            body=body,
            elapsed_time=time.time() - start_time,
            size=len(body.encode("utf-8")),
        )
    finally:
        response.close()

    count = len(events)
    if count > 0:
        summary = f"SSE stream opened. Received {count} event(s)."
        summary += f" First: {events[0]}"
    else:
        summary = (
            "SSE stream opened. No events received within timeout. Connection may be idle."
        )
    return ResponseData(
        status_code=200,
        headers=resp_headers,
        body=summary,
        elapsed_time=elapsed,
        size=len(summary.encode("utf-8")),
    )
