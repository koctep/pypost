import requests
import time
import json
from typing import Dict, Any, Callable, Optional
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.core.template_service import template_service
from pypost.core.metrics import MetricsManager

class HTTPClient:
    def __init__(self):
        self.session = requests.Session()

    def _prepare_request_kwargs(self, request_data: RequestData, variables: Dict[str, str]) -> Dict[str, Any]:
        """Prepares the arguments for requests.request by rendering templates."""
        # Render templates
        url = template_service.render_string(request_data.url, variables)
        
        headers = {}
        for k, v in request_data.headers.items():
            rendered_k = template_service.render_string(k, variables)
            rendered_v = template_service.render_string(v, variables)
            headers[rendered_k] = rendered_v

        params = {}
        for k, v in request_data.params.items():
            rendered_k = template_service.render_string(k, variables)
            rendered_v = template_service.render_string(v, variables)
            params[rendered_k] = rendered_v

        body = template_service.render_string(request_data.body, variables)

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

    def send_request(self, request_data: RequestData, variables: Dict[str, str] = None, 
                    stream_callback: Callable[[str], None] = None,
                    stop_flag: Callable[[], bool] = None,
                    headers_callback: Callable[[int, Dict], None] = None) -> ResponseData:
        if variables is None:
            variables = {}

        # 1. Prepare data (render templates and build kwargs)
        # 2. Execute request
        start_time = time.time()
        
        # Track request sent
        MetricsManager().track_request_sent(request_data.method)
        
        try:
            kwargs = self._prepare_request_kwargs(request_data, variables)
            response = self.session.request(**kwargs)
            
        except Exception as e:
            raise e

        if headers_callback:
            headers_callback(response.status_code, dict(response.headers))

        # Check for Transfer-Encoding: chunked. If so, and if we want to stream, we do so.
        # But 'requests' always returns a Response object immediately if stream=True.
        # So we can emit headers/status HERE if we had a callback for it.
        # But we don't have a callback for headers yet in send_request signature (only stream_callback for body).
        # We could add on_response_started callback.

        # Stream content
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
        MetricsManager().track_response_received(request_data.method, str(response.status_code))
        
        return ResponseData(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=content,
            elapsed_time=end_time - start_time,
            size=len(content.encode('utf-8')) # Calculate size from content
        )
