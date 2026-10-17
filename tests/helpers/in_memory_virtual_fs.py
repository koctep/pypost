"""In-memory virtual filesystem backend and storage adapters (PYPOST-1435).

Provides an ephemeral, thread-safe in-memory file and directory tree with
pathlib.Path method interception and pluggable in-memory storage adapters
for CollectionVariablesIntegrationHarness.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
import fnmatch
import io
import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any, Optional
import uuid

from pypost.core.library_connection_store import LibraryConnectionStore
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.core.storage import EnvironmentSerializeStats, StorageManager
from pypost.models.library_manager import LibraryConnectionRecord
from pypost.models.library_manifest import LocalLibraryOverlay
from pypost.models.models import Environment

logger = logging.getLogger(__name__)

# Module-level registry and lock for active mounted in-memory filesystems
_ACTIVE_MOUNTS: list[InMemoryVirtualFS] = []
_GLOBAL_LOCK = threading.RLock()
_ORIGINAL_PATH_METHODS: dict[str, Any] = {}

INTERCEPTED_METHODS = (
    "mkdir",
    "read_text",
    "write_text",
    "read_bytes",
    "write_bytes",
    "exists",
    "is_file",
    "is_dir",
    "iterdir",
    "glob",
    "rglob",
    "unlink",
    "stat",
    "open",
)


def _match_parts(rel_parts: tuple[str, ...], pat_parts: tuple[str, ...]) -> bool:
    """Match path parts against glob pattern parts supporting recursive **."""
    if len(pat_parts) == 0:
        return len(rel_parts) == 0
    if pat_parts[0] == "**":
        if len(pat_parts) == 1:
            return True
        for i in range(len(rel_parts) + 1):
            if _match_parts(rel_parts[i:], pat_parts[1:]):
                return True
        return False
    if len(rel_parts) == 0:
        return False
    if fnmatch.fnmatchcase(rel_parts[0], pat_parts[0]):
        return _match_parts(rel_parts[1:], pat_parts[1:])
    return False


@dataclass
class VirtualNode:
    """Base node in virtual filesystem tree."""

    name: str
    parent: Optional[VirtualDir] = None
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)

    def is_file(self) -> bool:
        return False

    def is_dir(self) -> bool:
        return False

    def stat(self) -> os.stat_result:
        now = int(self.modified_at)
        created = int(self.created_at)
        return os.stat_result((0o100644, 1, 1, 1, 1000, 1000, 0, now, now, created))


@dataclass
class VirtualFile(VirtualNode):
    """Leaf node representing an in-memory file."""

    content: bytes = b""

    def is_file(self) -> bool:
        return True

    def is_dir(self) -> bool:
        return False

    def read_text(self, encoding: str = "utf-8", errors: str = "strict") -> str:
        return self.content.decode(encoding=encoding, errors=errors)

    def write_text(
        self,
        data: str,
        encoding: str = "utf-8",
        errors: str = "strict",
    ) -> int:
        self.content = data.encode(encoding=encoding, errors=errors)
        self.modified_at = time.time()
        return len(data)

    def read_bytes(self) -> bytes:
        return self.content

    def write_bytes(self, data: bytes) -> int:
        self.content = data
        self.modified_at = time.time()
        return len(data)

    def stat(self) -> os.stat_result:
        now = int(self.modified_at)
        created = int(self.created_at)
        mode = 0o100644
        return os.stat_result(
            (mode, 1, 1, 1, 1000, 1000, len(self.content), now, now, created)
        )


@dataclass
class VirtualDir(VirtualNode):
    """Interior node representing an in-memory directory."""

    children: dict[str, VirtualNode] = field(default_factory=dict)

    def is_file(self) -> bool:
        return False

    def is_dir(self) -> bool:
        return True

    def get_child(self, name: str) -> Optional[VirtualNode]:
        return self.children.get(name)

    def add_child(self, node: VirtualNode) -> VirtualNode:
        node.parent = self
        self.children[node.name] = node
        self.modified_at = time.time()
        return node

    def remove_child(self, name: str) -> Optional[VirtualNode]:
        removed = self.children.pop(name, None)
        if removed is not None:
            removed.parent = None
            self.modified_at = time.time()
        return removed

    def count_nodes(self) -> int:
        """Recursively count all virtual nodes rooted at this directory."""
        total = 1
        for child in self.children.values():
            if isinstance(child, VirtualDir):
                total += child.count_nodes()
            else:
                total += 1
        return total

    def total_bytes(self) -> int:
        """Recursively compute total payload bytes stored under this directory."""
        total = 0
        for child in self.children.values():
            if isinstance(child, VirtualFile):
                total += len(child.content)
            elif isinstance(child, VirtualDir):
                total += child.total_bytes()
        return total

    def stat(self) -> os.stat_result:
        now = int(self.modified_at)
        created = int(self.created_at)
        mode = 0o040755
        return os.stat_result((mode, 1, 1, 1, 1000, 1000, 4096, now, now, created))


class _VirtualTextIOWrapper(io.StringIO):
    """Context-managed text IO buffer that flushes to InMemoryVirtualFS on close."""

    def __init__(
        self,
        vfs: InMemoryVirtualFS,
        path: Path,
        encoding: str = "utf-8",
        errors: str = "strict",
    ) -> None:
        super().__init__()
        self._vfs = vfs
        self._path = path
        self._encoding = encoding
        self._errors = errors

    def close(self) -> None:
        if not self.closed:
            self._vfs.write_text(
                self._path,
                self.getvalue(),
                encoding=self._encoding,
                errors=self._errors,
            )
        super().close()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.close()


class _VirtualBytesIOWrapper(io.BytesIO):
    """Context-managed bytes IO buffer that flushes to InMemoryVirtualFS on close."""

    def __init__(self, vfs: InMemoryVirtualFS, path: Path) -> None:
        super().__init__()
        self._vfs = vfs
        self._path = path

    def close(self) -> None:
        if not self.closed:
            self._vfs.write_bytes(self._path, self.getvalue())
        super().close()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.close()


class InMemoryVirtualFS:
    """In-memory virtual filesystem engine with transparent Path interception."""

    root_path: Path
    _root_node: VirtualDir
    _lock: threading.RLock
    _is_mounted: bool
    _ops_count: dict[str, int]

    def __init__(self, root_path: Path | str | None = None) -> None:
        if root_path is None:
            self.root_path = Path(f"/virtual_pypost_harness_{uuid.uuid4().hex}").resolve()
        else:
            self.root_path = Path(root_path).resolve()

        self._root_node = VirtualDir(name="", parent=None)
        self._lock = threading.RLock()
        self._is_mounted = False
        self._ops_count = {
            "mkdir": 0,
            "read_text": 0,
            "write_text": 0,
            "read_bytes": 0,
            "write_bytes": 0,
            "unlink": 0,
            "exists": 0,
            "stat": 0,
            "iterdir": 0,
            "glob": 0,
        }

    def get_metrics(self) -> dict[str, Any]:
        """Return operational metrics and resource counters for virtual filesystem.

        Key metrics:
        - mcp.harness.virtual_fs.ops_total: Total operations saved vs physical disk
        - mcp.harness.virtual_fs.nodes_count: Current count of virtual directory and file nodes
        - mcp.harness.virtual_fs.bytes_total: Total payload bytes held in memory
        - mcp.harness.virtual_fs.ops_by_type: Granular breakdown by operation
        """
        with self._lock:
            total_ops = sum(self._ops_count.values())
            nodes = self._root_node.count_nodes()
            byte_size = self._root_node.total_bytes()
            return {
                "mcp.harness.virtual_fs.ops_total": total_ops,
                "mcp.harness.virtual_fs.nodes_count": nodes,
                "mcp.harness.virtual_fs.bytes_total": byte_size,
                "mcp.harness.virtual_fs.ops_by_type": dict(self._ops_count),
            }

    def is_in_virtual_root(self, path: Path | str) -> bool:
        """Check whether the given path resides within this virtual filesystem root."""
        try:
            p_str = str(Path(path).resolve())
        except Exception:
            p_str = str(path)
        root_str = str(self.root_path)
        return p_str == root_str or p_str.startswith(root_str.rstrip("/") + "/")

    def _get_relative_parts(self, path: Path | str) -> tuple[str, ...]:
        p = Path(path)
        if not p.is_absolute():
            p = self.root_path / p
        else:
            p = p.resolve()

        try:
            rel = p.relative_to(self.root_path)
            return rel.parts
        except ValueError:
            return ()

    def _find_node(self, path: Path | str) -> Optional[VirtualNode]:
        parts = self._get_relative_parts(path)
        if not parts:
            return self._root_node

        current: VirtualNode = self._root_node
        for part in parts:
            if not isinstance(current, VirtualDir):
                logger.error(
                    "Virtual filesystem hierarchy corruption: expected directory node "
                    "for %s in %s, found %s",
                    part,
                    path,
                    type(current).__name__,
                )
                return None
            child = current.get_child(part)
            if child is None:
                return None
            current = child
        return current

    def mkdir(
        self,
        path: Path | str,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        with self._lock:
            self._ops_count["mkdir"] += 1
            logger.debug(
                "mkdir path=%s parents=%s exist_ok=%s",
                path,
                parents,
                exist_ok,
            )
            parts = self._get_relative_parts(path)
            if not parts:
                if not exist_ok:
                    raise FileExistsError(f"Directory already exists: {path}")
                return

            current: VirtualDir = self._root_node
            for index, part in enumerate(parts):
                child = current.get_child(part)
                is_last = index == len(parts) - 1
                if child is not None:
                    if not isinstance(child, VirtualDir):
                        raise FileExistsError(f"Not a directory: {part}")
                    if is_last and not exist_ok:
                        raise FileExistsError(f"Directory already exists: {path}")
                    current = child
                else:
                    if not is_last and not parents:
                        raise FileNotFoundError(f"Parent directory not found: {path}")
                    new_dir = VirtualDir(name=part)
                    current.add_child(new_dir)
                    current = new_dir

    def write_text(
        self,
        path: Path | str,
        text: str,
        encoding: str = "utf-8",
        errors: str = "strict",
    ) -> int:
        with self._lock:
            self._ops_count["write_text"] += 1
            logger.debug("write_text path=%s bytes=%d", path, len(text))
            parts = self._get_relative_parts(path)
            if not parts:
                raise IsADirectoryError(f"Cannot write text to root directory: {path}")

            current: VirtualDir = self._root_node
            for part in parts[:-1]:
                child = current.get_child(part)
                if child is None or not isinstance(child, VirtualDir):
                    raise FileNotFoundError(f"Parent directory not found for: {path}")
                current = child

            file_name = parts[-1]
            existing = current.get_child(file_name)
            if existing is not None:
                if isinstance(existing, VirtualDir):
                    raise IsADirectoryError(f"Path is a directory: {path}")
                assert isinstance(existing, VirtualFile)
                return existing.write_text(text, encoding=encoding, errors=errors)

            new_file = VirtualFile(name=file_name)
            new_file.write_text(text, encoding=encoding, errors=errors)
            current.add_child(new_file)
            return len(text)

    def read_text(
        self,
        path: Path | str,
        encoding: str = "utf-8",
        errors: str = "strict",
    ) -> str:
        with self._lock:
            self._ops_count["read_text"] += 1
            node = self._find_node(path)
            if node is None:
                raise FileNotFoundError(f"No such file: {path}")
            if isinstance(node, VirtualDir):
                raise IsADirectoryError(f"Path is a directory: {path}")
            assert isinstance(node, VirtualFile)
            content = node.read_text(encoding=encoding, errors=errors)
            logger.debug("read_text path=%s bytes=%d", path, len(content))
            return content

    def write_bytes(self, path: Path | str, data: bytes) -> int:
        with self._lock:
            self._ops_count["write_bytes"] += 1
            logger.debug("write_bytes path=%s bytes=%d", path, len(data))
            parts = self._get_relative_parts(path)
            if not parts:
                raise IsADirectoryError(f"Cannot write bytes to root directory: {path}")

            current: VirtualDir = self._root_node
            for part in parts[:-1]:
                child = current.get_child(part)
                if child is None or not isinstance(child, VirtualDir):
                    raise FileNotFoundError(f"Parent directory not found for: {path}")
                current = child

            file_name = parts[-1]
            existing = current.get_child(file_name)
            if existing is not None:
                if isinstance(existing, VirtualDir):
                    raise IsADirectoryError(f"Path is a directory: {path}")
                assert isinstance(existing, VirtualFile)
                return existing.write_bytes(data)

            new_file = VirtualFile(name=file_name)
            new_file.write_bytes(data)
            current.add_child(new_file)
            return len(data)

    def read_bytes(self, path: Path | str) -> bytes:
        with self._lock:
            self._ops_count["read_bytes"] += 1
            node = self._find_node(path)
            if node is None:
                raise FileNotFoundError(f"No such file: {path}")
            if isinstance(node, VirtualDir):
                raise IsADirectoryError(f"Path is a directory: {path}")
            assert isinstance(node, VirtualFile)
            content = node.read_bytes()
            logger.debug("read_bytes path=%s bytes=%d", path, len(content))
            return content

    def exists(self, path: Path | str) -> bool:
        with self._lock:
            self._ops_count["exists"] += 1
            return self._find_node(path) is not None

    def is_file(self, path: Path | str) -> bool:
        with self._lock:
            node = self._find_node(path)
            return node is not None and node.is_file()

    def is_dir(self, path: Path | str) -> bool:
        with self._lock:
            node = self._find_node(path)
            return node is not None and node.is_dir()

    def unlink(self, path: Path | str, missing_ok: bool = False) -> None:
        with self._lock:
            self._ops_count["unlink"] += 1
            logger.debug("unlink path=%s missing_ok=%s", path, missing_ok)
            parts = self._get_relative_parts(path)
            if not parts:
                raise PermissionError(f"Cannot unlink root directory: {path}")

            current: VirtualDir = self._root_node
            for part in parts[:-1]:
                child = current.get_child(part)
                if child is None or not isinstance(child, VirtualDir):
                    if missing_ok:
                        logger.warning(
                            "Virtual parent missing on unlink (ignored missing_ok=True): %s",
                            path,
                        )
                        return
                    raise FileNotFoundError(f"No such file: {path}")
                current = child

            file_name = parts[-1]
            existing = current.get_child(file_name)
            if existing is None:
                if missing_ok:
                    logger.warning(
                        "Virtual file missing on unlink (ignored missing_ok=True): %s",
                        path,
                    )
                    return
                raise FileNotFoundError(f"No such file: {path}")

            if isinstance(existing, VirtualDir):
                raise IsADirectoryError(f"Path is a directory: {path}")

            current.remove_child(file_name)

    def stat(self, path: Path | str) -> os.stat_result:
        with self._lock:
            self._ops_count["stat"] += 1
            node = self._find_node(path)
            if node is None:
                raise FileNotFoundError(f"No such file or directory: {path}")
            return node.stat()

    def iterdir(self, path: Path | str) -> Iterator[Path]:
        with self._lock:
            self._ops_count["iterdir"] += 1
            node = self._find_node(path)
            if node is None:
                raise FileNotFoundError(f"No such directory: {path}")
            if not isinstance(node, VirtualDir):
                raise NotADirectoryError(f"Not a directory: {path}")

            base = Path(path)
            return iter([base / child_name for child_name in node.children.keys()])

    def glob(self, path: Path | str, pattern: str) -> Iterator[Path]:
        with self._lock:
            self._ops_count["glob"] += 1
            base_node = self._find_node(path)
            if base_node is None or not isinstance(base_node, VirtualDir):
                return iter([])

            base_path = Path(path)
            pat_parts = tuple(p for p in pattern.split("/") if p)

            results: list[Path] = []

            def _walk(current: VirtualDir, rel_parts: tuple[str, ...]) -> None:
                for name, child in current.children.items():
                    child_rel = rel_parts + (name,)
                    if _match_parts(child_rel, pat_parts):
                        results.append(base_path.joinpath(*child_rel))
                    if isinstance(child, VirtualDir):
                        _walk(child, child_rel)

            _walk(base_node, ())
            return iter(results)

    def rglob(self, path: Path | str, pattern: str) -> Iterator[Path]:
        if pattern.startswith("**/"):
            return self.glob(path, pattern)
        return self.glob(path, f"**/{pattern}")

    def open(
        self,
        path: Path | str,
        mode: str = "r",
        encoding: str | None = None,
        errors: str | None = None,
    ) -> Any:
        p = Path(path)
        enc = encoding or "utf-8"
        err = errors or "strict"

        if "r" in mode and "+" not in mode:
            if "b" in mode:
                return io.BytesIO(self.read_bytes(p))
            return io.StringIO(self.read_text(p, encoding=enc, errors=err))

        if "w" in mode:
            if "b" in mode:
                return _VirtualBytesIOWrapper(self, p)
            return _VirtualTextIOWrapper(self, p, encoding=enc, errors=err)

        if "a" in mode:
            if "b" in mode:
                existing_bytes = self.read_bytes(p) if self.exists(p) else b""
                buf = _VirtualBytesIOWrapper(self, p)
                buf.write(existing_bytes)
                return buf
            existing_text = self.read_text(p, encoding=enc, errors=err) if self.exists(p) else ""
            tbuf = _VirtualTextIOWrapper(self, p, encoding=enc, errors=err)
            tbuf.write(existing_text)
            return tbuf

        raise ValueError(f"Unsupported mode for virtual filesystem open(): {mode}")

    def mount(self) -> InMemoryVirtualFS:
        """Activate Path method interception for paths under root_path."""
        with _GLOBAL_LOCK:
            if not self._is_mounted:
                if not _ACTIVE_MOUNTS:
                    _install_path_hooks()
                _ACTIVE_MOUNTS.append(self)
                self._is_mounted = True
                logger.info("Mounted InMemoryVirtualFS at %s", self.root_path)
        return self

    def unmount(self) -> None:
        """Deactivate interception and restore standard Path methods if no mounts remain."""
        with _GLOBAL_LOCK:
            if self._is_mounted:
                if self in _ACTIVE_MOUNTS:
                    _ACTIVE_MOUNTS.remove(self)
                self._is_mounted = False
                logger.info("Unmounted InMemoryVirtualFS at %s", self.root_path)
                if not _ACTIVE_MOUNTS:
                    _uninstall_path_hooks()

    def clear(self) -> None:
        """Release all in-memory nodes and reclaim memory."""
        with self._lock:
            self._root_node = VirtualDir(name="", parent=None)
            self._ops_count = {k: 0 for k in self._ops_count}
            logger.debug("Cleared InMemoryVirtualFS root=%s", self.root_path)

    def __enter__(self) -> InMemoryVirtualFS:
        return self.mount()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.unmount()
        self.clear()


def _find_vfs_for_path(path: Path | str) -> Optional[InMemoryVirtualFS]:
    """Find the active mounted virtual filesystem responsible for the given path."""
    with _GLOBAL_LOCK:
        for vfs in _ACTIVE_MOUNTS:
            if vfs.is_in_virtual_root(path):
                return vfs
    return None


def _install_path_hooks() -> None:
    """Install interception hooks on pathlib.Path."""
    if _ORIGINAL_PATH_METHODS:
        return

    for method_name in INTERCEPTED_METHODS:
        original = getattr(Path, method_name)
        _ORIGINAL_PATH_METHODS[method_name] = original

    def _make_hook(name: str) -> Any:
        orig = _ORIGINAL_PATH_METHODS[name]

        def _hook(self: Path, *args: Any, **kwargs: Any) -> Any:
            vfs = _find_vfs_for_path(self)
            if vfs is not None:
                vfs_method = getattr(vfs, name)
                return vfs_method(self, *args, **kwargs)
            return orig(self, *args, **kwargs)

        return _hook

    for method_name in INTERCEPTED_METHODS:
        setattr(Path, method_name, _make_hook(method_name))
    logger.debug("Installed pathlib.Path interception hooks for InMemoryVirtualFS")


def _uninstall_path_hooks() -> None:
    """Restore original pathlib.Path methods."""
    for method_name, orig in list(_ORIGINAL_PATH_METHODS.items()):
        setattr(Path, method_name, orig)
    _ORIGINAL_PATH_METHODS.clear()
    logger.debug("Restored original pathlib.Path methods after InMemoryVirtualFS unmount")


# =============================================================================
# In-Memory Storage Adapters
# =============================================================================


class InMemoryLibraryConnectionStore(LibraryConnectionStore):
    """In-memory adapter for LibraryConnectionStore with zero physical disk I/O."""

    vfs: InMemoryVirtualFS
    _records: list[LibraryConnectionRecord]

    def __init__(
        self,
        vfs: InMemoryVirtualFS,
        path: Path | str | None = None,
        legacy_base_dir: Path | str | None = None,
    ) -> None:
        target_path = Path(path or (vfs.root_path / "connections.json"))
        super().__init__(path=target_path, legacy_base_dir=legacy_base_dir)
        self.vfs = vfs
        self._records = []

    def load(
        self,
        legacy_base_dir: Optional[Path | str] = None,
    ) -> list[LibraryConnectionRecord]:
        """Load connection records from in-memory cache or virtual filesystem."""
        if not self._records and self.vfs.is_file(self.path):
            try:
                raw_text = self.vfs.read_text(self.path)
                data = json.loads(raw_text)
                raw_records = (
                    data.get("connections", data) if isinstance(data, dict) else data
                )
                if isinstance(raw_records, list):
                    self._records = [
                        LibraryConnectionRecord.model_validate(r) for r in raw_records
                    ]
            except Exception as exc:
                logger.warning("Failed to load in-memory library connections: %s", exc)
        return list(self._records)

    def save(self, records: list[LibraryConnectionRecord]) -> None:
        """Persist connection records to memory cache and virtual filesystem."""
        self._records = list(records)
        payload = {
            "connections": [r.model_dump(mode="json") for r in records],
            "disconnected": [],
        }
        self.vfs.mkdir(self.path.parent, parents=True, exist_ok=True)
        self.vfs.write_text(self.path, json.dumps(payload, indent=2))

    def add(self, record: LibraryConnectionRecord) -> LibraryConnectionRecord:
        """Add connection record to in-memory store after duplicate validation."""
        records = self.load()
        if any(item.stable_id == record.stable_id for item in records):
            raise ValueError("A library with this identity is already connected.")
        if any(item.canonical_path == record.canonical_path for item in records):
            raise ValueError("This local directory is already connected.")
        if record.manifest_id and any(
            item.manifest_id == record.manifest_id for item in records
        ):
            raise ValueError("A library with this identity is already connected.")
        records.append(record)
        self.save(records)
        return record

    def remove(self, stable_id: str) -> bool:
        """Remove connection record from in-memory store."""
        records = self.load()
        remaining = [item for item in records if item.stable_id != stable_id]
        if len(remaining) == len(records):
            return False
        self.save(remaining)
        return True


class InMemoryLocalOverlayManager(LocalOverlayManager):
    """In-memory adapter for LocalOverlayManager bypassing OS chmod and file locks."""

    vfs: InMemoryVirtualFS
    _overlays: dict[str, LocalLibraryOverlay]

    def __init__(
        self,
        vfs: InMemoryVirtualFS,
        base_dir: Path | str | None = None,
        secrets_codec: Any = None,
    ) -> None:
        target_dir = Path(base_dir or (vfs.root_path / "libraries_data"))
        super().__init__(base_dir=target_dir, secrets_codec=secrets_codec)
        self.vfs = vfs
        self._overlays = {}

    def get_overlay(self, library_id: str) -> LocalLibraryOverlay:
        """Retrieve local overlay from volatile memory or virtual storage."""
        if library_id in self._overlays:
            return self._overlays[library_id].model_copy(deep=True)

        target_file = self._overlay_path(library_id)
        if self.vfs.is_file(target_file):
            try:
                data = json.loads(self.vfs.read_text(target_file))
                overlay = LocalLibraryOverlay(**data)
                self._overlays[library_id] = overlay
                return overlay.model_copy(deep=True)
            except Exception as exc:
                logger.warning("Failed to load overlay from VFS for %s: %s", library_id, exc)

        return LocalLibraryOverlay(library_id=library_id)

    def save_overlay(self, overlay: LocalLibraryOverlay) -> Path:
        """Save local overlay in memory and virtual filesystem without OS permission calls."""
        self._overlays[overlay.library_id] = overlay.model_copy(deep=True)
        target_file = self._overlay_path(overlay.library_id)
        self.vfs.mkdir(target_file.parent, parents=True, exist_ok=True)
        self.vfs.write_text(target_file, overlay.model_dump_json(indent=2))
        return target_file

    def delete_overlay(self, library_id: str) -> bool:
        """Remove overlay from memory and virtual filesystem."""
        existed = library_id in self._overlays
        self._overlays.pop(library_id, None)
        target_file = self._overlay_path(library_id)
        if self.vfs.exists(target_file):
            self.vfs.unlink(target_file, missing_ok=True)
            return True
        return existed


class InMemoryStorageManager(StorageManager):
    """In-memory adapter for StorageManager bypassing atomic temporary file rename."""

    vfs: InMemoryVirtualFS
    _environments: list[Environment]

    def __init__(
        self,
        vfs: InMemoryVirtualFS,
        data_dir: Path | str | None = None,
        **kwargs: Any,
    ) -> None:
        target_dir = Path(data_dir or (vfs.root_path / "workspace"))
        super().__init__(
            data_dir=target_dir,
            initialize_collections=False,
            initialize_environments=False,
            **kwargs,
        )
        self.vfs = vfs
        self._environments = []

    def load_environments(self) -> list[Environment]:
        """Load workspace environments from in-memory state or virtual environments file."""
        if not self._environments and self.vfs.is_file(self.environments_file):
            try:
                raw_text = self.vfs.read_text(self.environments_file)
                data = json.loads(raw_text)
                if isinstance(data, list):
                    self._environments = [
                        Environment.model_validate(item) for item in data
                    ]
            except Exception as exc:
                logger.warning("Failed to load environments from VFS: %s", exc)
        return [env.model_copy(deep=True) for env in self._environments]

    def save_environments(
        self,
        environments: list[Environment],
        *,
        target_envelope_version: int | None = None,
    ) -> EnvironmentSerializeStats:
        """Persist environments in volatile memory and mirror to virtual filesystem."""
        self._environments = [env.model_copy(deep=True) for env in environments]
        stats = EnvironmentSerializeStats()
        data: list[dict[str, Any]] = []

        for env in environments:
            serialized, env_stats = self._env_adapter.serialize_environment(
                env,
                target_envelope_version=target_envelope_version,
            )
            stats += env_stats
            data.append(serialized)
            self._env_adapter.remember_environment_state(
                env.id,
                serialized.get("variables", {}),
                dict(env.variables),
            )

        self.vfs.mkdir(self.environments_file.parent, parents=True, exist_ok=True)
        self.vfs.write_text(self.environments_file, json.dumps(data, indent=2))
        return stats


__all__ = [
    "InMemoryLibraryConnectionStore",
    "InMemoryLocalOverlayManager",
    "InMemoryStorageManager",
    "InMemoryVirtualFS",
    "VirtualDir",
    "VirtualFile",
    "VirtualNode",
]
