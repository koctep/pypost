import requests
import time
import json
from typing import Dict, Any
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.core.template_service import template_service

class HTTPClient:
    def __init__(self):
        self.session = requests.Session()

    def send_request(self, request_data: RequestData, variables: Dict[str, str] = None) -> ResponseData:
        if variables is None:
            variables = {}

        # 1. Prepare data (render templates)
        url = template_service.render_string(request_data.url, variables)

        # Render headers
        headers = {}
        for k, v in request_data.headers.items():
            rendered_k = template_service.render_string(k, variables)
            rendered_v = template_service.render_string(v, variables)
            headers[rendered_k] = rendered_v

        # Render params
        params = {}
        for k, v in request_data.params.items():
            rendered_k = template_service.render_string(k, variables)
            rendered_v = template_service.render_string(v, variables)
            params[rendered_k] = rendered_v

        # Render body
        body = template_service.render_string(request_data.body, variables)

        # 2. Execute request
        start_time = time.time()
        try:
            response = self.session.request(
                method=request_data.method,
                url=url,
                headers=headers,
                params=params,
                data=body if request_data.body_type != 'json' else None,
                json=json.loads(body) if request_data.body_type == 'json' and body else None
            )
        except json.JSONDecodeError:
             # Fallback if body is not valid JSON but type is json (send as string/data)
             # Or maybe raise error? For now, let's try sending as raw data if json fails
             response = self.session.request(
                method=request_data.method,
                url=url,
                headers=headers,
                params=params,
                data=body
            )
        except Exception as e:
            # Re-raise or return error response
            raise e

        end_time = time.time()

        # 3. Process response
        return ResponseData(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=response.text,
            elapsed_time=end_time - start_time,
            size=len(response.content)
        )
