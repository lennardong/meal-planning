# BlobStore Concepts Guide

## What is a BlobStore?

A **BlobStore** is a low-level storage abstraction that handles opaque binary data (blobs). Think of it as a simple key-value store where:
- **Keys** are strings (paths like `user123/ingredients.json`)
- **Values** are raw bytes

The BlobStore doesn't know or care about:
- What format the data is in (JSON, Parquet, images, etc.)
- What domain the data represents (ingredients, plans, etc.)
- Who the user is (that's encoded in the key)

## Why Bytes, Not Dicts?

Many storage abstractions work with dictionaries or structured data. Our BlobStore works with raw bytes for several reasons:

1. **True Genericity**: Works with any format - JSON today, Parquet tomorrow
2. **Clear Responsibilities**: Serialization is the caller's job, not the store's
3. **Easy Swapping**: Same interface for filesystem, S3, GCS, Azure Blob Storage
4. **Quant-Ready**: Aligns with data engineering patterns where blobs are ingested and queried separately

## The Interface

```python
class BlobStore(Protocol):
    """Low-level blob storage. Format-agnostic, domain-agnostic."""

    def save_blob(self, key: str, data: bytes) -> None:
        """Save bytes to storage."""
        ...

    def load_blob(self, key: str) -> bytes | None:
        """Load bytes from storage. Returns None if not found."""
        ...

    def delete_blob(self, key: str) -> None:
        """Delete blob if exists."""
        ...

    def list_blobs(self, prefix: str = "") -> list[str]:
        """List all blob keys matching prefix."""
        ...

    def exists(self, key: str) -> bool:
        """Check if blob exists."""
        ...
```

## Key Structure

Keys are paths that encode context:

```
{user_id}/{entity}.{format}
```

Examples:
- `default/ingredients.json`
- `user123/dishes.json`
- `default/plans.json`

### Why Include Format in Key?

1. **Self-Describing**: Know the content type without reading headers
2. **Tool Compatibility**: DuckDB, Pandas can infer format from extension
3. **Future Migration**: Add `.parquet` alongside `.json` when needed
4. **Glob Queries**: `SELECT * FROM 'data/*/ingredients.json'`

## Implementations

### LocalFilesystemBlobStore

The current implementation uses the local filesystem:

```python
class LocalFilesystemBlobStore:
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def save_blob(self, key: str, data: bytes) -> None:
        path = self.base_path / key
        path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write via temp file
        tmp = path.with_suffix('.tmp')
        tmp.write_bytes(data)
        tmp.replace(path)

    def load_blob(self, key: str) -> bytes | None:
        path = self.base_path / key
        return path.read_bytes() if path.exists() else None
```

### Future Implementations

The same interface can be implemented for cloud storage:

- `S3BlobStore` - Amazon S3
- `GCSBlobStore` - Google Cloud Storage
- `AzureBlobStore` - Azure Blob Storage
- `MemoryBlobStore` - For testing

## Services Handle Serialization

Services sit above the BlobStore and handle:
- JSON encoding/decoding
- Key construction with user_id
- Domain model validation

```python
class CatalogueService:
    def __init__(self, store: BlobStore, user_id: str = "default"):
        self.store = store
        self.user_id = user_id

    def _key(self, filename: str) -> str:
        return f"{self.user_id}/{filename}"

    def save(self) -> None:
        # Encode to JSON bytes, save to blob store
        self.store.save_blob(
            self._key("ingredients.json"),
            json.dumps(self._ingredients, indent=2).encode('utf-8')
        )
```

## When to Use DuckDB

BlobStore is for write-path storage. When you need analytics:

```
Write Path: Services → BlobStore → Filesystem
Read Path (analytics): DuckDB → Parquet/JSON files
```

DuckDB can query JSON files directly:
```sql
SELECT * FROM 'data/*/ingredients.json'
```

Add DuckDB when you need:
- Aggregations across users
- Complex queries
- Analytics dashboards

## Design Patterns

### Atomic Writes

Always use temp files for safe writes:
```python
tmp = path.with_suffix('.tmp')
tmp.write_bytes(data)
tmp.replace(path)  # Atomic on most filesystems
```

### Lazy Loading

Services lazy-load data on first access:
```python
def _ensure_loaded(self) -> None:
    if self._loaded:
        return
    data = self.store.load_blob(self._key("ingredients.json"))
    # ... parse and cache
    self._loaded = True
```

### User Scoping

User isolation is just key prefixing:
```python
def _key(self, filename: str) -> str:
    return f"{self.user_id}/{filename}"
```

## File Structure

```
data/
└── {user_id}/                    # Default: "default"
    ├── ingredients.json          # {"ING-xxx": {...}, ...}
    ├── dishes.json               # {"DISH-xxx": {...}, ...}
    ├── plans.json                # {"PLAN-2025-01": {...}, ...}
    └── contexts.json             # {"CTX-xxx": {...}, ...}
```

## Summary

| Layer | Responsibility |
|-------|----------------|
| BlobStore | Move bytes by key |
| Services | JSON + key construction |
| Core | Pure domain models |

The BlobStore is intentionally simple - it's just bytes and keys. All the smarts live in the services layer above it.
