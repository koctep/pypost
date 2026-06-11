import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

import requests

from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.template_service import TemplateService
from pypost.core.yaml_json_converter import (
    YamlBodyConversionError,
    convert_yaml_body_to_object,
)
from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.models.models import RequestData
from pypost.models.response import ResponseData

logger = logging.getLogger(__name__)

SSE_PROBE_TIMEOUT = 10.0
SSE_PROBE_CONNECT_TIMEOUT = 3.0
SSE_PROBE_MAX_EVENTS = 5
DEFAULT_REQUEST_TIMEOUT = 30.0


@dataclass(frozen=True)
class ResolvedRequestFields:
    """Template-resolved URL, headers, and body sent on the wire."""

    url: str
    headers: Dict[str, str]
    body: str


@dataclass(frozen=True)
class HTTPRequestResult:
    """HTTP transport outcome plus resolved request fields for history reuse."""

    response: ResponseData
    resolved: ResolvedRequestFields


class HTTPClient:
    def __init__(
        self,
        metrics: MetricsTrackerProtocol | None = None,
        template_service: TemplateService | None = None,
        session: requests.Session | None = None,
    ):
        self.session = session if session is not None else requests.Session()
        self._metrics = resolve_metrics(metrics)
        self._template_service = (
            template_service if template_service is not None else TemplateService()
        )
        if session is not None:
            logger.debug("HTTPClient: using injected requests.Session id=%d", id(session))
        if template_service is not None:
            logger.debug("HTTPClient: using injected TemplateService id=%d", id(template_service))
        else:
            logger.debug("HTTPClient: using default TemplateService")

    def _prepare_request_kwargs(
        self,
        request_data: RequestData,
        variables: Dict[str, str],
        rendered_url: str | None = None,
    ) -> tuple[Dict[str, Any], ResolvedRequestFields]:
        """Prepares the arguments for requests.request by rendering templates."""
        url = (
            rendered_url
            if rendered_url is not None
            else self._template_service.render_string(request_data.url, variables)
        )

        headers = {}
        for k, v in request_data.headers.items():
            rendered_k = self._template_service.render_string(k, variables)
            rendered_v = self._template_service.render_string(v, variables)
            headers[rendered_k] = rendered_v

        params = {}
        for k, v in request_data.params.items():
            rendered_k = self._template_service.render_string(k, variables)
            rendered_v = self._template_service.render_string(v, variables)
            params[rendered_k] = rendered_v

        body = self._template_service.render_string(request_data.body, variables)
        stripped_body = body.strip()

        # Prepare kwargs
        kwargs = {
            "method": request_data.method,
            "url": url,
            "headers": headers,
            "params": params,
            "stream": True,
            "timeout": DEFAULT_REQUEST_TIMEOUT,
        }

        if request_data.body_type == "yaml" and request_data.yaml_as_json and stripped_body:
            try:
                kwargs["json"] = convert_yaml_body_to_object(body)
            except YamlBodyConversionError as exc:
                logger.error(
                    "yaml_to_json_conversion_failed method=%s url=%r detail=%s",
                    request_data.method,
                    url,
                    exc,
                )
                self._metrics.track_yaml_to_json_conversion_failed()
                raise ExecutionError(
                    category=ErrorCategory.BODY,
                    message="Could not convert YAML body to JSON.",
                    detail=str(exc),
                ) from exc
        elif request_data.body_type == "json" and stripped_body:
            try:
                kwargs["json"] = json.loads(body)
            except json.JSONDecodeError:
                kwargs["data"] = body
        elif request_data.body_type != "json" and stripped_body:
            kwargs["data"] = body

        resolved = ResolvedRequestFields(url=url, headers=dict(headers), body=body)
        return kwargs, resolved

    def _handle_sse_response(
        self, response, request_data: RequestData, start_time: float
    ) -> ResponseData:
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
                "SSE stream opened. No events received within timeout. " "Connection may be idle."
            )
        return ResponseData(
            status_code=200,
            headers=resp_headers,
            body=summary,
            elapsed_time=elapsed,
            size=len(summary.encode("utf-8")),
        )

    def send_request(
        self,
        request_data: RequestData,
        variables: Dict[str, str] = None,
        stream_callback: Callable[[str], None] = None,
        stop_flag: Callable[[], bool] = None,
        headers_callback: Callable[[int, Dict], None] = None,
    ) -> HTTPRequestResult:
        if variables is None:
            variables = {}

        start_time = time.time()
        self._metrics.track_request_sent(request_data.method)

        url = self._template_service.render_string(request_data.url, variables)
        is_sse_endpoint = request_data.method == "GET" and "/sse" in url.rstrip("/")
        if is_sse_endpoint:
            logger.debug("sse_probe_detected method=%s url=%s", request_data.method, url)

        try:
            kwargs, resolved = self._prepare_request_kwargs(
                request_data, variables, rendered_url=url
            )
            if is_sse_endpoint:
                kwargs["timeout"] = (SSE_PROBE_CONNECT_TIMEOUT, SSE_PROBE_TIMEOUT)
                headers = dict(kwargs.get("headers", {}))
                headers.setdefault("Accept", "text/event-stream")
                kwargs["headers"] = headers
            response = self.session.request(**kwargs)
        except requests.Timeout as exc:
            logger.error("Request timed out: %s %s", request_data.method, url)
            raise ExecutionError(
                category=ErrorCategory.TIMEOUT,
                message=f"Request to {url} timed out.",
                detail=str(exc),
            ) from exc
        except requests.ConnectionError as exc:
            logger.error("Connection failed: %s %s", request_data.method, url)
            raise ExecutionError(
                category=ErrorCategory.NETWORK,
                message=f"Could not connect to {url}.",
                detail=str(exc),
            ) from exc
        except requests.RequestException as exc:
            logger.error("Request failed: %s %s — %s", request_data.method, url, exc)
            raise ExecutionError(
                category=ErrorCategory.UNKNOWN,
                message="An unexpected request error occurred.",
                detail=str(exc),
            ) from exc

        if headers_callback:
            headers_callback(response.status_code, dict(response.headers))

        content_type = response.headers.get("Content-Type", "")
        if request_data.method == "GET" and (
            "text/event-stream" in content_type or is_sse_endpoint
        ):
            return HTTPRequestResult(
                response=self._handle_sse_response(response, request_data, start_time),
                resolved=resolved,
            )

        content_parts = []
        # iter_content with None uses optimal chunk size from server (or fallback).
        # Default yields bytes; decode here so mocks and real responses stay aligned.
        for chunk in response.iter_content(chunk_size=None):
            if stop_flag and stop_flag():
                # If cancelled, we break the loop.
                # Note: This stops reading, but doesn't necessarily close socket immediately
                # unless we close response.
                response.close()
                break

            if chunk:
                if isinstance(chunk, bytes):
                    chunk = chunk.decode("utf-8", errors="replace")
                content_parts.append(chunk)
                if stream_callback:
                    stream_callback(chunk)

            # Check stop flag again after processing chunk to be responsive
            if stop_flag and stop_flag():
                response.close()
                break

        content = "".join(content_parts)

        end_time = time.time()

        # 3. Process response
        self._metrics.track_response_received(request_data.method, str(response.status_code))
        logger.debug(
            "request_complete method=%s status=%d elapsed_ms=%.0f size=%d",
            request_data.method,
            response.status_code,
            (end_time - start_time) * 1000,
            len(content.encode("utf-8")),
        )
        return HTTPRequestResult(
            response=ResponseData(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=content,
                elapsed_time=end_time - start_time,
                size=len(content.encode("utf-8")),
            ),
            resolved=resolved,
        )
