from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

import requests

from pypost.core.http_response_body_reader import read_streamed_body
from pypost.core.sensitive_text_sanitizer import sanitize_text
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.template_service import TemplateService
from pypost.core.yaml_json_converter import (
    YamlBodyConversionError,
    convert_yaml_body_to_object,
)
from pypost.core.request_fields import ResolvedRequestFields
from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.models.models import RequestData
from pypost.models.response import ResponseData

logger = logging.getLogger(__name__)

SSE_PROBE_TIMEOUT = 10.0
SSE_PROBE_CONNECT_TIMEOUT = 3.0
SSE_PROBE_MAX_EVENTS = 5
DEFAULT_REQUEST_TIMEOUT = 30.0
DEFAULT_MAX_RESPONSE_BYTES = 52_428_800  # 50 MiB
TRUNCATION_NOTICE = "\n\n[Response body truncated: exceeded max_response_bytes limit]"


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
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    ):
        self.session = session if session is not None else requests.Session()
        self._metrics = resolve_metrics(metrics)
        self._max_response_bytes = max_response_bytes
        self._template_service = (
            template_service if template_service is not None else TemplateService()
        )
        if session is not None:
            logger.debug("HTTPClient: using injected requests.Session id=%d", id(session))
        if template_service is not None:
            logger.debug("HTTPClient: using injected TemplateService id=%d", id(template_service))
        else:
            logger.debug("HTTPClient: using default TemplateService")

    @staticmethod
    def _error_log_url(url: str, variables: Dict[str, str]) -> str:
        """Return a URL safe for ERROR logs (heuristic + env-value redaction)."""
        env_vars = {key: str(value) for key, value in variables.items()}
        return sanitize_text(url, env_vars=env_vars)

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
                    self._error_log_url(url, variables),
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
        variables: Dict[str, str] | None = None,
        stream_callback: Callable[[str], None] | None = None,
        stop_flag: Callable[[], bool] | None = None,
        headers_callback: Callable[[int, Dict], None] | None = None,
    ) -> HTTPRequestResult:
        if variables is None:
            variables = {}

        start_time = time.time()
        self._metrics.track_request_sent(request_data.method)

        url = self._template_service.render_string(request_data.url, variables)

        try:
            kwargs, resolved = self._prepare_request_kwargs(
                request_data, variables, rendered_url=url
            )
            if request_data.method == "GET" and _headers_accept_event_stream(
                kwargs.get("headers", {})
            ):
                kwargs["timeout"] = (SSE_PROBE_CONNECT_TIMEOUT, SSE_PROBE_TIMEOUT)
                headers = dict(kwargs.get("headers", {}))
                headers.setdefault("Accept", "text/event-stream")
                kwargs["headers"] = headers
            response = self.session.request(**kwargs)
        except requests.Timeout as exc:
            logger.error(
                "http_request_timed_out method=%s url=%r",
                request_data.method,
                self._error_log_url(url, variables),
            )
            raise ExecutionError(
                category=ErrorCategory.TIMEOUT,
                message=f"Request to {url} timed out.",
                detail=str(exc),
            ) from exc
        except requests.ConnectionError as exc:
            logger.error(
                "http_connection_failed method=%s url=%r",
                request_data.method,
                self._error_log_url(url, variables),
            )
            raise ExecutionError(
                category=ErrorCategory.NETWORK,
                message=f"Could not connect to {url}.",
                detail=str(exc),
            ) from exc
        except requests.RequestException as exc:
            logger.error(
                "http_request_failed method=%s url=%r detail=%s",
                request_data.method,
                self._error_log_url(url, variables),
                exc,
            )
            raise ExecutionError(
                category=ErrorCategory.UNKNOWN,
                message="An unexpected request error occurred.",
                detail=str(exc),
            ) from exc

        if headers_callback:
            headers_callback(response.status_code, dict(response.headers))

        content_type = response.headers.get("Content-Type", "")
        if request_data.method == "GET" and _is_sse_content_type(content_type):
            logger.debug(
                "sse_stream_detected method=%s url=%s content_type=%s",
                request_data.method,
                url,
                content_type,
            )
            return HTTPRequestResult(
                response=self._handle_sse_response(response, request_data, start_time),
                resolved=resolved,
            )

        content, truncated = read_streamed_body(
            response,
            max_response_bytes=self._max_response_bytes,
            stream_callback=stream_callback,
            stop_flag=stop_flag,
        )
        if truncated:
            self._metrics.track_response_body_truncated(request_data.method)
            logger.warning(
                "response_body_truncated method=%s url=%s max_bytes=%d",
                request_data.method,
                url,
                self._max_response_bytes,
            )
            content = f"{content}{TRUNCATION_NOTICE}"

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
