"""Format detection for response body payloads (Content-Type + heuristics)."""

from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET

import yaml

from pypost.ui.widgets.fold.fold_region import BodyFormat

logger = logging.getLogger(__name__)


def detect_body_format(
    headers: dict[str, str] | None,
    body: str,
) -> BodyFormat:
    """Determine the BodyFormat from Content-Type or payload heuristics."""
    if headers:
        for key, val in headers.items():
            if key.lower() == "content-type":
                ct = val.lower().split(";")[0].strip()
                if (
                    ct in ("application/json", "text/json")
                    or ct.startswith("application/")
                    and ct.endswith("+json")
                ):
                    logger.debug(
                        "detect_body_format detected=json source=header content_type=%s", ct
                    )
                    return BodyFormat.JSON
                if ct in (
                    "application/x-yaml",
                    "text/yaml",
                    "application/yaml",
                    "text/x-yaml",
                ):
                    logger.debug(
                        "detect_body_format detected=yaml source=header content_type=%s", ct
                    )
                    return BodyFormat.YAML
                if (
                    ct in ("application/xml", "text/xml")
                    or ct.startswith("application/")
                    and ct.endswith("+xml")
                ):
                    logger.debug(
                        "detect_body_format detected=xml source=header content_type=%s", ct
                    )
                    return BodyFormat.XML

    stripped = body.strip()
    if not stripped:
        return BodyFormat.PLAIN

    # Heuristic 1: JSON
    if (stripped.startswith("{") and stripped.endswith("}")) or (
        stripped.startswith("[") and stripped.endswith("]")
    ):
        try:
            json.loads(stripped)
            logger.debug(
                "detect_body_format detected=json source=heuristic length=%d", len(stripped)
            )
            return BodyFormat.JSON
        except (json.JSONDecodeError, ValueError):
            pass

    # Heuristic 2: XML
    if stripped.startswith("<") and stripped.endswith(">"):
        try:
            ET.fromstring(stripped)
            logger.debug(
                "detect_body_format detected=xml source=heuristic length=%d", len(stripped)
            )
            return BodyFormat.XML
        except ET.ParseError:
            pass

    # Heuristic 3: YAML
    if "\n" in stripped and ":" in stripped:
        try:
            parsed = yaml.safe_load(stripped)
            if isinstance(parsed, (dict, list)):
                logger.debug(
                    "detect_body_format detected=yaml source=heuristic length=%d", len(stripped)
                )
                return BodyFormat.YAML
        except yaml.YAMLError:
            pass

    logger.debug("detect_body_format detected=plain source=fallback length=%d", len(stripped))
    return BodyFormat.PLAIN
