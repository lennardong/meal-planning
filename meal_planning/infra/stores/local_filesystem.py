"""Local filesystem blob store implementation.

Implements the BlobStore protocol using the local filesystem.
Keys map to file paths under a base directory.
"""

from __future__ import annotations

from pathlib import Path


class LocalFilesystemBlobStore:
    """BlobStore implementation using local filesystem.

    Keys are paths relative to base_path.
    Example: key="default/ingredients.json" -> base_path/default/ingredients.json
    """

    def __init__(self, base_path: Path):
        """Initialize the store.

        Args:
            base_path: Root directory for all blob storage.
        """
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        """Resolve key to absolute path."""
        return self.base_path / key

    def save_blob(self, key: str, data: bytes) -> None:
        """Save bytes to storage.

        Uses atomic write via temp file for safety.

        Args:
            key: Full path like 'default/ingredients.json'.
            data: Raw bytes to store.
        """
        path = self._resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp, then rename
        tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            tmp.write_bytes(data)
            tmp.replace(path)
        except Exception:
            # Clean up temp file on failure
            if tmp.exists():
                tmp.unlink()
            raise

    def load_blob(self, key: str) -> bytes | None:
        """Load bytes from storage.

        Args:
            key: Full path like 'default/ingredients.json'.

        Returns:
            Raw bytes if found, None if not found.
        """
        path = self._resolve_path(key)
        if not path.exists():
            return None
        return path.read_bytes()

    def delete_blob(self, key: str) -> None:
        """Delete blob if exists.

        Args:
            key: Full path like 'default/ingredients.json'.
        """
        path = self._resolve_path(key)
        if path.exists():
            path.unlink()

    def list_blobs(self, prefix: str = "") -> list[str]:
        """List all blob keys matching prefix.

        Args:
            prefix: Key prefix to filter by (e.g., 'default/').

        Returns:
            List of matching keys (relative to base_path).
        """
        if prefix:
            search_path = self.base_path / prefix
            if not search_path.exists():
                return []
            # If prefix is a directory, list its contents
            if search_path.is_dir():
                return [
                    str(p.relative_to(self.base_path))
                    for p in search_path.rglob("*")
                    if p.is_file()
                ]
            # If prefix is a partial path, find matching files
            parent = search_path.parent
            name_prefix = search_path.name
            if parent.exists():
                return [
                    str(p.relative_to(self.base_path))
                    for p in parent.iterdir()
                    if p.is_file() and p.name.startswith(name_prefix)
                ]
            return []
        else:
            # List all files
            return [
                str(p.relative_to(self.base_path))
                for p in self.base_path.rglob("*")
                if p.is_file()
            ]

    def exists(self, key: str) -> bool:
        """Check if blob exists.

        Args:
            key: Full path like 'default/ingredients.json'.

        Returns:
            True if blob exists.
        """
        return self._resolve_path(key).exists()
