"""Unified JSON selector path evaluation engine for response masking (PYPOST-1394)."""

from __future__ import annotations

import logging
import re
from typing import Any, Iterable, Sequence

logger = logging.getLogger(__name__)

HIDDEN_PLACEHOLDER: str = "***"

_HEADER_PREFIX = "header:"
_BRACKET_WILDCARD_RE = re.compile(r"\[\*\]")


class CompiledPathSelector:
    """Represents a compiled hierarchical JSON path selector pattern."""

    def __init__(self, raw: str) -> None:
        self.raw = raw
        self.tokens: tuple[str, ...] = self._parse_tokens(raw)

    @staticmethod
    def _parse_tokens(raw: str) -> tuple[str, ...]:
        # Normalize items[*].secret -> items.*.secret -> ['items', '*', 'secret']
        normalized = _BRACKET_WILDCARD_RE.sub(".*.", raw)
        tokens = [t for t in normalized.split(".") if t]
        return tuple(tokens)

    def matches(self, candidate_tokens: Sequence[str]) -> bool:
        if len(self.tokens) != len(candidate_tokens):
            return False
        for expected, actual in zip(self.tokens, candidate_tokens):
            if expected == "*":
                continue
            if expected != actual:
                return False
        return True


class JsonSelectorEngine:
    """Evaluates JSON selector path rules and performs data redaction."""

    def __init__(self, selectors: Iterable[str] | None = None) -> None:
        self._raw_selectors: set[str] = set()
        self._bare_keys: set[str] = set()
        self._path_selectors: list[CompiledPathSelector] = []
        if selectors:
            self._compile(selectors)

    @property
    def is_empty(self) -> bool:
        return not self._bare_keys and not self._path_selectors

    def _compile(self, selectors: Iterable[str]) -> None:
        for s in selectors:
            if not s or not isinstance(s, str):
                continue
            cleaned = s.strip()
            if not cleaned or cleaned.lower().startswith(_HEADER_PREFIX):
                continue
            self._raw_selectors.add(cleaned)
            if "." not in cleaned and "[" not in cleaned:
                self._bare_keys.add(cleaned)
            else:
                self._path_selectors.append(CompiledPathSelector(cleaned))
        logger.debug(
            "json_selector_engine_compiled raw_count=%d bare_keys_count=%d path_selectors_count=%d",
            len(self._raw_selectors),
            len(self._bare_keys),
            len(self._path_selectors),
        )

    def matches(self, path: Sequence[str], key: str) -> bool:
        """Determines if a key at the given path matches any configured selector."""
        if self.is_empty:
            return False
        key_str = str(key)
        if key_str in self._bare_keys:
            return True
        if not self._path_selectors:
            return False

        candidate_tokens = [str(t) for t in path] + [key_str]
        for rule in self._path_selectors:
            if rule.matches(candidate_tokens):
                return True

        # Shorthand dot fallback compatibility (e.g. items.secret matching items.*.secret)
        shorthand_tokens = [t for t in candidate_tokens if t != "*"]
        if shorthand_tokens != candidate_tokens:
            for rule in self._path_selectors:
                if rule.matches(shorthand_tokens):
                    return True

        return False

    def redact_tree(
        self,
        node: Any,
        placeholder: str = HIDDEN_PLACEHOLDER,
    ) -> tuple[Any, int]:
        """Recursively redacts matching keys in dictionaries and lists."""
        if self.is_empty or not isinstance(node, (dict, list)):
            return node, 0
        masked_count = [0]
        redacted = self._redact_node(node, [], placeholder, masked_count)
        logger.debug(
            "json_selector_engine_redact_tree_completed masked_count=%d",
            masked_count[0],
        )
        return redacted, masked_count[0]

    def _redact_node(
        self,
        node: Any,
        path: list[str],
        placeholder: str,
        masked_count: list[int],
    ) -> Any:
        if isinstance(node, dict):
            res: dict[str, Any] = {}
            for key, val in node.items():
                key_str = str(key)
                if self.matches(path, key_str):
                    res[key] = placeholder
                    masked_count[0] += 1
                else:
                    res[key] = self._redact_node(
                        val, path + [key_str], placeholder, masked_count
                    )
            return res
        if isinstance(node, list):
            return [
                self._redact_node(item, path + ["*"], placeholder, masked_count)
                for item in node
            ]
        return node

    @staticmethod
    def canonical_path(path: Sequence[str], key: str) -> str:
        """Generates canonical dot-notation path string."""
        return ".".join(list(path) + [str(key)])

    @staticmethod
    def format_path_variants(path: Sequence[str], key: str) -> set[str]:
        """Backward-compatible helper generating path variant strings."""
        tokens = [str(t) for t in path] + [str(key)]
        full_dot = ".".join(tokens)
        shorthand_tokens = [t for t in tokens if t != "*"]
        shorthand_dot = ".".join(shorthand_tokens)
        wildcard_parts: list[str] = []
        for t in tokens:
            if t == "*":
                if wildcard_parts:
                    wildcard_parts[-1] = f"{wildcard_parts[-1]}[*]"
                else:
                    wildcard_parts.append("[*]")
            else:
                wildcard_parts.append(t)
        wildcard_dot = ".".join(wildcard_parts)
        return {str(key), full_dot, shorthand_dot, wildcard_dot}
