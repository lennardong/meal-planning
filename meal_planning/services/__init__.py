"""Application services layer.

This layer contains:
- Port definitions (interfaces for infrastructure)
- Application services (orchestrate domain operations with I/O)

Services handle:
- JSON serialization/deserialization
- User-scoped key construction for blob storage
- Coordination between multiple domain operations
"""
