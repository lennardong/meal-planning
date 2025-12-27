"""Core domain layer - pure models and operations.

This layer contains:
- Domain models (immutable value objects and entities)
- Domain enumerations
- Pure domain operations (no I/O)
- Shared types (Result, errors)

No I/O allowed in this layer - all I/O happens in services and infra.
"""
