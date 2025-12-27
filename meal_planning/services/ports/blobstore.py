"""BlobStore port - storage abstraction for bytes.

The BlobStore is a low-level abstraction for storing and retrieving
opaque binary data (blobs). It doesn't know about JSON, users, or domains.
Keys are paths, data is bytes.

Implementations:
- LocalFilesystemBlobStore (infra/stores/local_filesystem.py)
- Future: S3BlobStore, GCSBlobStore, AzureBlobStore
"""

from typing import Protocol


class BlobStore(Protocol):
    """Low-level blob storage. Format-agnostic, domain-agnostic.

    Keys are paths like 'user123/ingredients.json'.
    Data is raw bytes - serialization is caller's responsibility.
    """

    def save_blob(self, key: str, data: bytes) -> None:
        """Save bytes to storage.

        Args:
            key: Full path like 'default/ingredients.json'.
            data: Raw bytes to store.
        """
        ...

    def load_blob(self, key: str) -> bytes | None:
        """Load bytes from storage.

        Args:
            key: Full path like 'default/ingredients.json'.

        Returns:
            Raw bytes if found, None if not found.
        """
        ...

    def delete_blob(self, key: str) -> None:
        """Delete blob if exists.

        Args:
            key: Full path like 'default/ingredients.json'.
        """
        ...

    def list_blobs(self, prefix: str = "") -> list[str]:
        """List all blob keys matching prefix.

        Args:
            prefix: Key prefix to filter by (e.g., 'default/').

        Returns:
            List of matching keys.
        """
        ...

    def exists(self, key: str) -> bool:
        """Check if blob exists.

        Args:
            key: Full path like 'default/ingredients.json'.

        Returns:
            True if blob exists.
        """
        ...
