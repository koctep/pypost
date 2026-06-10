import logging
import shlex
import subprocess
import sys
import urllib.parse

from pypost.core.template_service import TemplateService
from pypost.models.models import HistoryEntry, RequestData

logger = logging.getLogger(__name__)


class CurlGenerator:
    """Generates a cURL command string from request data."""

    @staticmethod
    def generate(
        request: RequestData, variables: dict, template_service: TemplateService
    ) -> str:
        """Generates a valid cURL command string from the request data and variables."""
        method = template_service.render_string(
            request.method, variables, render_path="curl"
        )
        url_rendered = template_service.render_string(
            request.url, variables, render_path="curl"
        )

        # Parse the rendered URL to merge with parameters
        parsed_url = urllib.parse.urlparse(url_rendered)
        existing_params = urllib.parse.parse_qsl(parsed_url.query)

        # Render the params from the request
        rendered_params = []
        for k, v in request.params.items():
            rendered_k = template_service.render_string(
                k, variables, render_path="curl"
            )
            rendered_v = template_service.render_string(
                v, variables, render_path="curl"
            )
            if rendered_k:
                rendered_params.append((rendered_k, rendered_v))

        # Merge params
        merged_params = existing_params + rendered_params
        new_query = urllib.parse.urlencode(merged_params)

        # Reconstruct the URL
        final_url = urllib.parse.urlunparse(
            (
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment,
            )
        )

        logger.debug("Generating cURL for %s %s", method, final_url)

        # Start building the curl command parts
        parts = ["curl", "-X", method, final_url]

        # Add headers
        for k, v in request.headers.items():
            rendered_k = template_service.render_string(
                k, variables, render_path="curl"
            )
            rendered_v = template_service.render_string(
                v, variables, render_path="curl"
            )
            if rendered_k:
                parts.append("-H")
                parts.append(f"{rendered_k}: {rendered_v}")

        # Add body
        if request.body:
            rendered_body = template_service.render_string(
                request.body, variables, render_path="curl"
            )
            if rendered_body:
                parts.append("-d")
                parts.append(rendered_body)

        if sys.platform == "win32":
            return subprocess.list2cmdline(parts)
        return shlex.join(parts)

    @staticmethod
    def generate_from_history(entry: HistoryEntry) -> str:
        """Generates a valid cURL command string from a resolved history entry."""
        logger.debug("Generating cURL from history for %s %s", entry.method, entry.url)

        parts = ["curl", "-X", entry.method, entry.url]

        for k, v in entry.headers.items():
            parts.append("-H")
            parts.append(f"{k}: {v}")

        if entry.body:
            parts.append("-d")
            parts.append(entry.body)

        if sys.platform == "win32":
            return subprocess.list2cmdline(parts)
        return shlex.join(parts)
