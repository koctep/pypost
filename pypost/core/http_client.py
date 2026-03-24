import logging
import requests
import time
import json
from typing import Dict, Any, Callable, List
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.core.template_service import TemplateService
from pypost.core.metrics import MetricsManager

logger = logging.getLogger(__name__)

SSE_PROBE_TIMEOUT = 10.0
SSE_PROBE_CONNECT_TIMEOUT = 3.0
SSE_PROBE_MAX_EVENTS = 5


class HTTPClient:
    def __init__(self, metrics: MetricsManager | None = None,
                 template_service: TemplateService | None = None):
        self.session = requests.Session()
        self._metrics = metrics
        self._template_service = template_service
        if template_service is not None:
            logger.debug("HTTPClient: using injected TemplateService id=%d", id(template_service))

    def _prepare_request_kwargs(self, request_data: RequestData, variables: Dict[str, str]) -> Dict[str, Any]:
        """Prepares the arguments for requests.request by rendering templates."""
        # Render templates
        url = self._template_service.render_string(request_data.url, variables)
        
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

        # Prepare kwargs
        kwargs = {
            'method': request_data.method,
            'url': url,
            'headers': headers,
            'params': params,
            'stream': True,
            'timeout': 30.0
        }
        
        if request_data.body_type == 'json' and body:
            try:
                kwargs['json'] = json.loads(body)
            except json.JSONDecodeError:
                kwargs['data'] = body
        elif request_data.body_type != 'json':
            kwargs['data'] = body
            
        return kwargs

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
                    desc += (
                        f": {data[:100]}..." if len(data) > 100 else f": {data}"
                    )
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
                "SSE stream opened. No events received within timeout. "
                "Connection may be idle."
            )
        return ResponseData(
            status_code=200,
            headers=resp_headers,
            body=summary,
            elapsed_time=elapsed,
            size=len(summary.encode("utf-8")),
        )

    def send_request(self, request_data: RequestData, variables: Dict[str, str] = None,
                    stream_callback: Callable[[str], None] = None,
                    stop_flag: Callable[[], bool] = None,
                    headers_callback: Callable[[int, Dict], None] = None) -> ResponseData:
        if variables is None:
            variables = {}

        start_time = time.time()
        if self._metrics:
            self._metrics.track_request_sent(request_data.method)

        url = self._template_service.render_string(request_data.url, variables)
        is_sse_endpoint = (
            request_data.method == "GET" and "/sse" in url.rstrip("/")
        )

        try:
            kwargs = self._prepare_request_kwargs(request_data, variables)
            if is_sse_endpoint:
                kwargs["timeout"] = (SSE_PROBE_CONNECT_TIMEOUT, SSE_PROBE_TIMEOUT)
                headers = dict(kwargs.get("headers", {}))
                headers.setdefault("Accept", "text/event-stream")
                kwargs["headers"] = headers
            response = self.session.request(**kwargs)
        except Exception as e:
            logger.error(
                "Request failed: %s %s — %s",
                request_data.method, url, e,
            )
            raise

        if headers_callback:
            headers_callback(response.status_code, dict(response.headers))

        content_type = response.headers.get("Content-Type", "")
        if request_data.method == "GET" and (
            "text/event-stream" in content_type or is_sse_endpoint
        ):
            return self._handle_sse_response(response, request_data, start_time)

        content_parts = []
        # iter_content with None uses optimal chunk size from server (or fallback)
        # decode_unicode=True yields strings instead of bytes
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if stop_flag and stop_flag():
                # If cancelled, we break the loop. 
                # Note: This stops reading, but doesn't necessarily close socket immediately unless we close response.
                response.close() 
                break
                
            if chunk:
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
        if self._metrics:
            self._metrics.track_response_received(request_data.method, str(response.status_code))
        
        return ResponseData(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=content,
            elapsed_time=end_time - start_time,
            size=len(content.encode('utf-8')) # Calculate size from content
        )
