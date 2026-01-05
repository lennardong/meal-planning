# Session Architecture: Multi-User Data Isolation in Palate

> How Palate isolates user data without a database, authentication, or server-side sessions.

**Scope Note:** This document covers web session management for multi-user support. While session threading touches both web and app layers, it's primarily driven by web deployment requirements (Cloud Run, stateless servers, browser-based users). For domain architecture, see [App Architecture](app-architecture.md). For UI patterns, see [Web Architecture](web-architecture.md).

## Table of Contents

- [The Problem We're Solving](#the-problem-were-solving)
- [The Session Threading Pattern](#the-session-threading-pattern)
- [Layer-by-Layer Walkthrough](#layer-by-layer-walkthrough)
- [Data Flow Diagrams](#data-flow-diagrams)
- [Code Pattern Reference](#code-pattern-reference)
- [Design Decisions](#design-decisions)
- [Longlist of Things to Do](#longlist-of-things-to-do)

---

## The Problem We're Solving

Hey there! Let me walk you through an interesting problem we solved. When we deployed Palate to Cloud Run, we faced a classic multi-user challenge:

**The constraints:**
- Multiple users hit the same Cloud Run instance simultaneously
- No database (we're keeping it simple)
- No authentication (this is a meal planner, not a bank)
- Data is ephemeral (resets on deploy, and that's fine)
- Users should see only their own dishes and plans

**What we wanted:**
- Anonymous sessions - no sign-up, no login
- Data isolation - my kimchi fried rice doesn't show up in your catalogue
- Persistence within a session - close browser, come back, data still there

The classic solution would be Flask sessions with a database backend, or JWT tokens with a session store. But that's a lot of machinery for a meal planning app. We went a different direction.

---

## The Session Threading Pattern

### Key Insight: This is NOT Middleware

Let's clear up a common misconception. You might think "multi-user support" means adding middleware that intercepts requests. That's not what we did.

**Traditional middleware pattern:**
```
Request → [Middleware extracts user] → Controller → Service → Database
                    ↓
            Server-side session store
```

**Our session threading pattern:**
```
Browser (owns session ID in localStorage)
    ↓
Dash callback receives session_id as State parameter
    ↓
AppContextManager caches per-session contexts
    ↓
Services use user-scoped file paths
    ↓
Filesystem: data/{session_id}/dishes.json
```

The crucial difference: **the client owns the session ID**. The server never generates or manages sessions. It simply routes to the right data based on what the client provides.

### The Five-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 1: BROWSER                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ localStorage["session-id-store"] = "abc123-uuid-here"               │    │
│  │                                                                     │    │
│  │ • Generated once on first visit                                     │    │
│  │ • Persists across tabs, browser restarts                            │    │
│  │ • Survives until user clears browser data                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ dcc.Store syncs to/from localStorage
                                     │ Callbacks receive via State("session-id-store", "data")
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 2: DASH CALLBACKS                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ def render_columns(..., session_id):                                 │    │
│  │     app_ctx = _get_context(session_id)  # <-- The key line!          │    │
│  │     dishes = app_ctx.catalogue.list_dishes()                         │    │
│  │                                                                     │    │
│  │ Every data-touching callback:                                        │    │
│  │ 1. Accepts session_id as State parameter                             │    │
│  │ 2. Calls _get_context(session_id) as first operation                 │    │
│  │ 3. Uses the returned context for all data access                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ _get_context() → get_user_context()
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 3: APP CONTEXT MANAGER                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ class AppContextManager:                                             │    │
│  │     _contexts: dict[str, AppContext] = {}  # In-memory cache         │    │
│  │                                                                     │    │
│  │     def get_context(self, user_id):                                  │    │
│  │         if user_id not in self._contexts:                            │    │
│  │             ctx = create_app_context(user_id=user_id)                │    │
│  │             if not ctx.catalogue.list_dishes():                      │    │
│  │                 self._copy_default_dishes(ctx)  # Onboarding!        │    │
│  │             self._contexts[user_id] = ctx                            │    │
│  │         return self._contexts[user_id]                               │    │
│  │                                                                     │    │
│  │ Why cache? Services lazy-load from disk. Without caching,            │    │
│  │ every callback = filesystem read. Cache = sub-millisecond access.    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ CatalogueService(store, user_id=session_id)
                                     │ PlanningService(store, user_id=session_id)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 4: SERVICES                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ class CatalogueService:                                              │    │
│  │     def __init__(self, store, user_id="default"):                    │    │
│  │         self._user_id = user_id                                      │    │
│  │                                                                     │    │
│  │     def _key(self, filename: str) -> str:                            │    │
│  │         return f"{self._user_id}/{filename}"                         │    │
│  │         # => "abc123-uuid-here/dishes.json"                          │    │
│  │                                                                     │    │
│  │ Every service operation uses _key() to scope to user's directory.    │    │
│  │ Same pattern in: CatalogueService, PlanningService, ContextService   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ store.save_blob("abc123-uuid/dishes.json", bytes)
                                     │ store.load_blob("abc123-uuid/dishes.json")
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 5: FILESYSTEM                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ data/                                                               │    │
│  │ ├── default/                  # CLI users, seed data                 │    │
│  │ │   ├── dishes.json                                                 │    │
│  │ │   ├── plans.json                                                  │    │
│  │ │   └── shortlist.json                                              │    │
│  │ │                                                                   │    │
│  │ ├── abc123-uuid-here/         # Browser user 1                       │    │
│  │ │   ├── dishes.json           # Their dishes                         │    │
│  │ │   ├── plans.json            # Their plans                          │    │
│  │ │   └── shortlist.json        # Their shortlist                      │    │
│  │ │                                                                   │    │
│  │ └── xyz789-uuid-here/         # Browser user 2                       │    │
│  │     ├── dishes.json           # Completely isolated                  │    │
│  │     ├── plans.json                                                  │    │
│  │     └── shortlist.json                                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer-by-Layer Walkthrough

### Layer 1: Client-Side Session Storage

The browser owns the session ID. This is stored in `localStorage`, which persists across:
- Tab closes
- Browser restarts
- System reboots

It does NOT persist across:
- Clearing browser data
- Different browsers
- Different devices

**Implementation:**

```python
# File: meal_planning/api/dash/app.py (line 84)

dcc.Store(id="session-id-store", data="", storage_type="local")
```

The `storage_type="local"` is critical. Dash's `dcc.Store` supports three modes:
- `"memory"` - Lost on page refresh (default)
- `"session"` - Lost when browser closes
- `"local"` - Persists until explicitly cleared

**Session ID Generation:**

```python
# File: meal_planning/api/dash/callbacks.py (lines 31-39)

@callback(
    Output("session-id-store", "data"),
    Input("session-id-store", "data"),
)
def init_session(session_id):
    """Generate session ID on first visit, stored in localStorage."""
    if not session_id:
        return str(uuid.uuid4())
    raise PreventUpdate
```

This callback fires once per browser. Here's the logic:
1. On first visit, `session_id` is empty string (from `data=""` in Store)
2. Empty string is falsy, so we generate a UUID and return it
3. Dash updates localStorage with the UUID
4. On subsequent visits, `session_id` has a value, so we `PreventUpdate` (do nothing)

**Why UUID?**
- Unique enough for our needs (collision probability is astronomically low)
- No coordination required (generated client-side)
- No server round-trip to get an ID
- Standard format that's easy to debug

### Layer 2: Callback Session Routing

Every callback that touches user data follows the same pattern.

**The Helper Function:**

```python
# File: meal_planning/api/dash/callbacks.py (lines 19-23)

def _get_context(session_id: str | None):
    """Get app context for session, falling back to default."""
    if session_id:
        return get_user_context(session_id)
    return get_app_context()
```

This helper:
1. Takes the session_id from the callback's State parameter
2. If we have a session_id, gets the user-specific context
3. Falls back to default context (for CLI or if somehow no session exists)

**Example Callback:**

```python
# File: meal_planning/api/dash/callbacks.py (lines 83-99)

@callback(
    Output("catalogue-cards", "children"),
    Output("catalogue-count", "children"),
    Output("shortlist-cards", "children"),
    Output("shortlist-count", "children"),
    Input("shortlist-store", "data"),
    Input("catalogue-search", "value"),
    Input("catalogue-cuisine-filter", "value"),
    Input("shortlist-search", "value"),
    Input("shortlist-cuisine-filter", "value"),
    State("session-id-store", "data"),  # <-- Always include this
)
def render_columns(shortlist_uids, cat_search, cat_cuisine, sl_search, sl_cuisine, session_id):
    """Re-render both columns when selection or filters change."""
    app_ctx = _get_context(session_id)  # <-- Always first line
    all_dishes = app_ctx.catalogue.list_dishes()  # Now user-scoped!
    # ... rest of callback
```

**The Pattern:**
1. Add `State("session-id-store", "data")` as the LAST parameter
2. Accept `session_id` as the last argument in the function signature
3. Call `_get_context(session_id)` as the first operation
4. Use `app_ctx` for all data access

### Layer 3: AppContextManager (The Heart)

This is where the magic happens. The `AppContextManager` maintains an in-memory cache of user contexts.

```python
# File: meal_planning/app.py (lines 144-177)

class AppContextManager:
    """Manages per-user application contexts for multi-user support.

    Each user session gets its own isolated context with separate data.
    New users automatically get a copy of the default dishes.
    """

    def __init__(self):
        self._contexts: dict[str, AppContext] = {}

    def get_context(self, user_id: str) -> AppContext:
        """Get or create context for a user."""
        if user_id not in self._contexts:
            ctx = create_app_context(user_id=user_id)
            # Copy default dishes for new users
            if not ctx.catalogue.list_dishes():
                self._copy_default_dishes(ctx)
            self._contexts[user_id] = ctx
        return self._contexts[user_id]

    def _copy_default_dishes(self, ctx: AppContext) -> None:
        """Copy dishes from default catalogue to new user."""
        default_ctx = create_app_context(user_id="default")
        for dish in default_ctx.catalogue.list_dishes():
            ctx.catalogue.add_dish(dish)
        ctx.catalogue.save()
```

**Key behaviors:**

1. **Lazy context creation**: Contexts are created on first access, not upfront
2. **In-memory caching**: Once created, contexts stay in `_contexts` dict
3. **New user onboarding**: First-time users get default dishes copied over
4. **Persistence**: `ctx.catalogue.save()` writes to user's directory

**Why cache in memory?**

Services lazy-load data from disk. Without caching:
```
callback → get_context() → create_app_context() → services load from disk
```

With caching (after first access):
```
callback → get_context() → return from _contexts dict (microseconds)
```

The trade-off is memory growth, but for a low-traffic app, this is fine.

### Layer 4: Service User Scoping

Every service constructs file paths using the user_id.

```python
# File: meal_planning/services/catalogue.py (lines 24-38)

class CatalogueService:
    def __init__(self, store: BlobStore, user_id: str = "default"):
        self._store = store
        self._user_id = user_id
        self._dishes: dict[str, Dish] = {}
        self._loaded = False

    def _key(self, filename: str) -> str:
        """Construct blob key with user scoping."""
        return f"{self._user_id}/{filename}"
```

The `_key()` method is the isolation mechanism. Every read/write goes through it:

```python
def save(self) -> None:
    self._store.save_blob(
        self._key("dishes.json"),  # => "abc123-uuid/dishes.json"
        json.dumps(...).encode()
    )
```

Same pattern in `PlanningService` and `ContextService`.

### Layer 5: Filesystem Isolation

The `LocalFilesystemBlobStore` treats keys as paths:

```python
# File: meal_planning/infra/stores/local_filesystem.py

class LocalFilesystemBlobStore:
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def _resolve_path(self, key: str) -> Path:
        return self.base_path / key
        # key = "abc123-uuid/dishes.json"
        # => data/abc123-uuid/dishes.json
```

Directories are created automatically on first write:
```python
def save_blob(self, key: str, data: bytes) -> None:
    path = self._resolve_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)  # Creates user dir
    # ... atomic write
```

---

## Data Flow Diagrams

### New User's First Visit

```
Browser                  Dash Callback            AppContextManager           Filesystem
   │                          │                          │                        │
   │  GET palate.io           │                          │                        │
   │─────────────────────────>│                          │                        │
   │                          │                          │                        │
   │  page loads              │                          │                        │
   │  session-id-store = ""   │                          │                        │
   │<─────────────────────────│                          │                        │
   │                          │                          │                        │
   │  init_session fires      │                          │                        │
   │  (session_id is empty)   │                          │                        │
   │                          │                          │                        │
   │  UUID generated          │                          │                        │
   │  "abc123-uuid"           │                          │                        │
   │  saved to localStorage   │                          │                        │
   │                          │                          │                        │
   │  render_columns fires    │                          │                        │
   │  session_id="abc123-uuid"│                          │                        │
   │─────────────────────────>│                          │                        │
   │                          │                          │                        │
   │                          │ get_user_context(        │                        │
   │                          │   "abc123-uuid")         │                        │
   │                          │─────────────────────────>│                        │
   │                          │                          │                        │
   │                          │                          │ user not in cache      │
   │                          │                          │ create_app_context()   │
   │                          │                          │───────────────────────>│
   │                          │                          │                        │
   │                          │                          │ load data/abc123-uuid/ │
   │                          │                          │ (doesn't exist)        │
   │                          │                          │<───────────────────────│
   │                          │                          │                        │
   │                          │                          │ _copy_default_dishes() │
   │                          │                          │───────────────────────>│
   │                          │                          │                        │
   │                          │                          │ mkdir abc123-uuid/     │
   │                          │                          │ write dishes.json      │
   │                          │                          │<───────────────────────│
   │                          │                          │                        │
   │                          │                          │ cache context          │
   │                          │<─────────────────────────│                        │
   │                          │                          │                        │
   │  dishes rendered         │                          │                        │
   │<─────────────────────────│                          │                        │
```

### Returning User (Same Browser)

```
Browser                  Dash Callback            AppContextManager           Filesystem
   │                          │                          │                        │
   │  GET palate.io           │                          │                        │
   │─────────────────────────>│                          │                        │
   │                          │                          │                        │
   │  page loads              │                          │                        │
   │  localStorage has        │                          │                        │
   │  "abc123-uuid"           │                          │                        │
   │                          │                          │                        │
   │  init_session fires      │                          │                        │
   │  (session_id exists)     │                          │                        │
   │  PreventUpdate           │                          │                        │
   │                          │                          │                        │
   │  render_columns fires    │                          │                        │
   │  session_id="abc123-uuid"│                          │                        │
   │─────────────────────────>│                          │                        │
   │                          │                          │                        │
   │                          │ get_user_context(        │                        │
   │                          │   "abc123-uuid")         │                        │
   │                          │─────────────────────────>│                        │
   │                          │                          │                        │
   │                          │                          │ user in cache!         │
   │                          │                          │ return cached context  │
   │                          │<─────────────────────────│  (no filesystem hit)   │
   │                          │                          │                        │
   │  dishes rendered         │                          │                        │
   │  (same as last time)     │                          │                        │
   │<─────────────────────────│                          │                        │
```

### Adding a Dish

```
Browser                  Dash Callback            CatalogueService            Filesystem
   │                          │                          │                        │
   │  clicks "Save Dish"      │                          │                        │
   │  session_id="abc123-uuid"│                          │                        │
   │─────────────────────────>│                          │                        │
   │                          │                          │                        │
   │                          │ ctx = _get_context(      │                        │
   │                          │   "abc123-uuid")         │                        │
   │                          │                          │                        │
   │                          │ ctx.catalogue.add_dish() │                        │
   │                          │─────────────────────────>│                        │
   │                          │                          │                        │
   │                          │                          │ _dishes[uid] = dish    │
   │                          │                          │ (in memory)            │
   │                          │                          │                        │
   │                          │ ctx.catalogue.save()     │                        │
   │                          │─────────────────────────>│                        │
   │                          │                          │                        │
   │                          │                          │ key = _key("dishes.json")
   │                          │                          │ # "abc123-uuid/dishes.json"
   │                          │                          │                        │
   │                          │                          │ store.save_blob(       │
   │                          │                          │   key, json_bytes)     │
   │                          │                          │───────────────────────>│
   │                          │                          │                        │
   │                          │                          │                        │ write to
   │                          │                          │                        │ data/abc123-uuid/
   │                          │                          │                        │   dishes.json
   │                          │                          │<───────────────────────│
   │                          │                          │                        │
   │  UI updated              │                          │                        │
   │<─────────────────────────│                          │                        │
```

---

## Code Pattern Reference

### Adding Session Support to a New Callback

If you're adding a new callback that accesses user data, follow this checklist:

```python
# CORRECT: Session-aware callback

@callback(
    Output("my-output", "children"),
    Input("my-trigger", "n_clicks"),
    State("session-id-store", "data"),  # Step 1: Add this State
)
def my_callback(n_clicks, session_id):  # Step 2: Accept session_id
    app_ctx = _get_context(session_id)  # Step 3: Get context first

    # Step 4: Use app_ctx for all data access
    dishes = app_ctx.catalogue.list_dishes()
    plans = app_ctx.planning.list_plans()

    # ... rest of your logic
```

### Common Mistakes

**Mistake 1: Forgetting the State parameter**
```python
# WRONG: No session_id parameter
@callback(
    Output("my-output", "children"),
    Input("my-trigger", "n_clicks"),
    # Missing: State("session-id-store", "data")
)
def my_callback(n_clicks):
    app_ctx = get_app_context()  # Uses default context!
    # All users see the same data...
```

**Mistake 2: Using get_app_context() instead of _get_context()**
```python
# WRONG: Ignores session_id
@callback(...)
def my_callback(n_clicks, session_id):
    app_ctx = get_app_context()  # Session_id ignored!
    # ...
```

**Mistake 3: Not passing session_id to helper functions**
```python
# WRONG: Helper doesn't receive session context
def helper_function():
    app_ctx = get_app_context()  # Back to default context
    # ...

@callback(...)
def my_callback(n_clicks, session_id):
    app_ctx = _get_context(session_id)
    helper_function()  # Oops, this uses wrong context
```

```python
# CORRECT: Pass context or session_id to helpers
def helper_function(app_ctx):
    # Use the passed context
    # ...

@callback(...)
def my_callback(n_clicks, session_id):
    app_ctx = _get_context(session_id)
    helper_function(app_ctx)  # Correct context used
```

---

## Design Decisions

### Why Not Traditional Server Sessions?

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| Flask sessions (cookies) | Standard, well-documented | Requires `SECRET_KEY`, server-side session storage | **REJECTED** |
| Database-backed sessions | Persistent, scalable | Need database, complexity | **REJECTED** |
| JWT tokens | Stateless, industry standard | Auth complexity, token refresh logic | **REJECTED** |
| Redis/Memcached sessions | Fast, shared across instances | Another service to manage | **REJECTED** |
| **localStorage UUID** | Simple, client-owned | Tied to browser, no cross-device | **CHOSEN** |

**The insight:** We don't need authentication. We need isolation. A UUID in localStorage gives us isolation without any of the auth complexity.

### Why Client-Owned Session IDs?

Traditional approach: Server generates session ID, sends to client via cookie.

Our approach: Client generates session ID, sends to server via callback State.

| Factor | Server-Generated | Client-Generated |
|--------|------------------|------------------|
| Coordination | Server must track sessions | No coordination needed |
| Statelessness | Server needs session store | Server is fully stateless |
| Cloud Run fit | Needs sticky sessions or shared store | Perfect fit (any instance works) |
| Complexity | Medium | Low |

**The insight:** Cloud Run instances are ephemeral. Server-side sessions need shared storage. Client-generated IDs mean any instance can handle any request.

### Why Cache Contexts in Memory?

Without caching, every callback would:
1. Create new service instances
2. Lazy-load data from filesystem
3. Parse JSON

With caching:
1. Return cached context (microseconds)

| Approach | Latency | Memory | Complexity |
|----------|---------|--------|------------|
| No cache | ~10-50ms per callback | Low | Low |
| **Memory cache** | ~0.01ms per callback | Grows with users | Low |
| Redis cache | ~1-5ms per callback | External service | Medium |

**Trade-off accepted:** Memory grows unbounded as users accumulate. For a low-traffic indie project, this is fine. If we scaled to thousands of concurrent users, we'd add LRU eviction.

### Why Copy Default Dishes for New Users?

When a new user arrives, their `data/{session-id}/` directory doesn't exist. We could:

1. **Start empty**: User sees blank catalogue, has to add dishes
2. **Copy defaults**: User sees starter dishes, can explore immediately

We chose option 2 for better UX. The `_copy_default_dishes()` method handles this:

```python
def _copy_default_dishes(self, ctx: AppContext) -> None:
    """Copy dishes from default catalogue to new user."""
    default_ctx = create_app_context(user_id="default")
    for dish in default_ctx.catalogue.list_dishes():
        ctx.catalogue.add_dish(dish)
    ctx.catalogue.save()
```

### Trade-offs We Accepted

| Trade-off | Why We Accept It |
|-----------|------------------|
| **No cross-device sync** | This is a meal planner, not Notion. Single device is fine for planning dinners. |
| **Data reset on deploy** | Ephemeral storage on Cloud Run is free. GCS/SQL costs money. Users get fresh defaults anyway. |
| **Memory growth** | AppContextManager cache grows unbounded. Acceptable for low traffic. |
| **No session expiry** | Old sessions accumulate on disk. Cleanup would add complexity. Deploy resets it. |
| **No session validation** | We accept any string as session_id. Malformed UUIDs just create odd directory names. |

---

## Longlist of Things to Do

Future improvements and cleanup ideas for the session architecture.

### Code Cleanup

- [ ] **Extract session routing to decorator**

  Currently `_get_context(session_id)` is repeated in every callback. Consider:
  ```python
  @with_session  # Decorator injects app_ctx
  def my_callback(..., app_ctx: AppContext):
      # app_ctx automatically resolved from session_id
  ```

- [ ] **Add session_id validation**

  Currently accepts any string. Add UUID format check:
  ```python
  def _get_context(session_id: str | None):
      if session_id and not is_valid_uuid(session_id):
          logger.warning(f"Invalid session_id format: {session_id}")
          return get_app_context()
      # ...
  ```

- [ ] **Add LRU eviction to AppContextManager**

  Contexts accumulate forever. Add `maxsize` with LRU eviction:
  ```python
  from functools import lru_cache

  @lru_cache(maxsize=1000)
  def get_context(self, user_id: str) -> AppContext:
      # ...
  ```

- [ ] **Add session cleanup job**

  Stale data directories accumulate. Add cleanup for sessions older than N days:
  ```bash
  find data/ -maxdepth 1 -type d -mtime +30 -exec rm -rf {} \;
  ```

### Architecture Enhancements

- [ ] **Session analytics**

  Track active sessions for capacity planning:
  - How many unique sessions per day?
  - How many concurrent?
  - Which sessions are heavy users?

- [ ] **Session export/import**

  Allow users to export their session data:
  ```python
  def export_session(session_id: str) -> bytes:
      """Export all user data as zip."""
      # Bundle dishes.json, plans.json, etc.
  ```

- [ ] **"Reset to defaults" per-session**

  UI button to reset a user's data to defaults without clearing localStorage.

- [ ] **Redis context cache for multi-instance**

  If scaling to multiple Cloud Run instances, in-memory cache won't share. Options:
  - Redis/Memcached for shared cache
  - Accept cache misses (each instance warms independently)
  - Sticky sessions (route user to same instance)

### Testing

- [ ] **Integration test for session isolation**

  Verify two sessions can't see each other's data:
  ```python
  def test_session_isolation():
      ctx_a = get_user_context("user-a")
      ctx_b = get_user_context("user-b")

      ctx_a.catalogue.add_dish(dish)

      assert dish.uid in [d.uid for d in ctx_a.catalogue.list_dishes()]
      assert dish.uid not in [d.uid for d in ctx_b.catalogue.list_dishes()]
  ```

- [ ] **Load test for concurrent sessions**

  Simulate 100 concurrent users, verify:
  - No data leakage between sessions
  - Memory usage stays reasonable
  - Latency stays acceptable

### Documentation

- [ ] **Document Cloud Run implications**

  - Cold start = empty cache
  - New instance = users reload from disk once
  - Deploy = all data reset (ephemeral disk)

- [ ] **Add Mermaid diagrams**

  ASCII art is portable but Mermaid renders nicely on GitHub.

---

## See Also

- [App Architecture](app-architecture.md) - Domain models and services layer
- [Web Architecture](web-architecture.md) - Dash UI, callbacks, styling
- [BlobStore Concepts](blobstore101.md) - How storage works
- [Main README](../../README.md) - Overall system design
- [DevOps README](../../devops/README.md) - Deployment and infrastructure
