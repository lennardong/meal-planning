# App Architecture: Domain Models & Services

> The business logic layer - how Palate models meal planning, independent of how users interact with it.

## Table of Contents

- [Why This Architecture?](#why-this-architecture)
- [The Domain Layer](#the-domain-layer)
- [The Services Layer](#the-services-layer)
- [Dependency Injection & Wiring](#dependency-injection--wiring)
- [Patterns I Used (and Why)](#patterns-i-used-and-why)
- [Mistakes I Avoided](#mistakes-i-avoided)
- [What I'd Do Differently](#what-id-do-differently)
- [Longlist of Things to Do](#longlist-of-things-to-do)

---

## Why This Architecture?

I've built systems that started simple and became unmaintainable. The pattern is always the same: business logic gets tangled with framework code, and suddenly you can't change your database without rewriting your UI. I didn't want that here.

**My goals were:**

1. **Framework independence** - I wanted business logic that doesn't know about Dash, Flask, or CLI. If I decide Dash was a mistake and switch to FastAPI + React, the domain layer shouldn't care.

2. **Storage agnosticism** - I wanted to swap from local filesystem to S3 or GCS by changing one adapter, not fifty files.

3. **Testable algorithms** - The meal distribution algorithm is the heart of this app. I wanted to test it with pure functions: same input, same output, no mocking HTTP requests.

**The approach I landed on:**

I borrowed three ideas and mashed them together:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLEAN ARCHITECTURE                                  │
│                                                                             │
│   Dependencies point inward. Core knows nothing about infrastructure.       │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         INFRASTRUCTURE                               │   │
│   │   LocalFilesystemBlobStore, ClaudeClient, Dash callbacks            │   │
│   │   ┌─────────────────────────────────────────────────────────────┐   │   │
│   │   │                        SERVICES                              │   │   │
│   │   │   CatalogueService, PlanningService, AIAssistantService     │   │   │
│   │   │   ┌─────────────────────────────────────────────────────┐   │   │   │
│   │   │   │                      CORE                            │   │   │   │
│   │   │   │   Dish, MealPlan, WeekPlan, Category, Cuisine       │   │   │   │
│   │   │   │   distribute_dishes(), assess_variety()              │   │   │   │
│   │   │   └─────────────────────────────────────────────────────┘   │   │   │
│   │   └─────────────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**From Clean Architecture:** Layers with clear dependencies. Core doesn't import services. Services don't import infrastructure.

**From Ports & Adapters:** Abstract interfaces (ports) that infrastructure implements (adapters). The `BlobStore` protocol doesn't care if it's backed by filesystem or S3.

**From Functional Programming:** Immutable models, pure functions for algorithms, explicit error handling with `Result` types instead of exceptions.

---

## The Domain Layer

The domain layer lives in `meal_planning/core/`. I organized it into four bounded contexts, each with its own models and operations:

```
core/
├── catalogue/          # What dishes exist
│   ├── models.py       # Dish entity
│   ├── enums.py        # Category, Cuisine, Region
│   ├── aggregate.py    # Catalogue (collection of dishes)
│   └── defaults.py     # 46 starter dishes
│
├── planning/           # How dishes become meal plans
│   ├── models.py       # MealPlan, WeekPlan, Shortlist
│   └── operations/     # Pure algorithms
│       ├── distribution.py
│       └── analysis.py
│
├── context/            # User preferences
│   ├── models.py       # UserContext
│   └── aggregate.py    # Preferences
│
└── shared/             # Cross-cutting types
    └── types.py        # Result[T, E], domain errors
```

### Catalogue Context

This is where I model "what dishes exist." The central entity is `Dish`:

```python
# core/catalogue/models.py:21-41

class Dish(BaseModel):
    """A dish in the catalogue."""

    model_config = ConfigDict(frozen=True)  # Immutable!

    uid: str = Field(default_factory=_dish_uid)
    name: str
    categories: tuple[Category, ...] = ()
    cuisine: Cuisine
    tags: tuple[str, ...] = ()
    recipe_reference: str = ""

    @property
    def region(self) -> Region:
        """Derive region from cuisine."""
        return CUISINE_REGION[self.cuisine]
```

**Why `frozen=True`?** I'll explain in the patterns section, but the short version: mutable models cause spooky bugs where you change something in one place and it mysteriously changes elsewhere. Immutability eliminates an entire class of bugs.

**Why `tuple` instead of `list`?** Tuples are immutable. If I used lists, someone could do `dish.categories.append(Category.GREENS)` and bypass the immutability. Tuples prevent that.

**The Enums (`core/catalogue/enums.py`):**

I use `StrEnum` for all domain enums. This was a deliberate choice:

```python
# core/catalogue/enums.py:10-35

class Category(StrEnum):
    """Food categories for dietary diversity tracking."""
    GREENS = "greens"
    LEGUMES = "legumes"
    GRAINS = "grains"
    ALLIUMS = "alliums"
    CRUCIFEROUS = "cruciferous"
    FRESH_HERBS = "fresh_herbs"
    SEEDS = "seeds"
    FERMENTED = "fermented"
    ROOT_VEG = "root_veg"
    DAIRY = "dairy"
```

**Why `StrEnum` over plain `Enum`?** JSON serialization. With `StrEnum`, the value serializes to `"greens"` instead of `"Category.GREENS"`. This makes the JSON files human-readable and editable.

**Domain knowledge as lookup tables:**

I encode domain knowledge in dictionaries rather than methods:

```python
# core/catalogue/enums.py:83-95

CUISINE_REGION: dict[Cuisine, Region] = {
    Cuisine.CHINESE: Region.EASTERN,
    Cuisine.JAPANESE: Region.EASTERN,
    Cuisine.KOREAN: Region.EASTERN,
    # ...
    Cuisine.ITALIAN: Region.WESTERN,
    Cuisine.FRENCH: Region.WESTERN,
    # ...
}
```

This lets the distribution algorithm enforce regional balance (2 Eastern + 2 Western per week) without the `Cuisine` enum knowing about distribution logic. Data, not behavior.

### Planning Context

This is where I model "how dishes become meal plans."

**The Entity vs. Value Object distinction:**

```python
# core/planning/models.py:21-46

class WeekPlan(BaseModel):
    """A week's worth of dishes. Value Object - no UID."""

    model_config = ConfigDict(frozen=True)
    dishes: tuple[str, ...] = ()  # Dish UIDs

    def with_dish(self, dish_uid: str) -> "WeekPlan":
        """Return new WeekPlan with dish added."""
        return WeekPlan(dishes=self.dishes + (dish_uid,))
```

```python
# core/planning/models.py:49-76

class MealPlan(BaseModel):
    """A complete meal plan. Entity - has UID."""

    model_config = ConfigDict(frozen=True)
    uid: str = Field(default_factory=_plan_uid)
    name: str = "Untitled Plan"
    weeks: tuple[WeekPlan, ...] = ()
```

**Why is `WeekPlan` a Value Object but `MealPlan` an Entity?**

- `WeekPlan` has no identity. Two week plans with the same dishes are equivalent. I don't care "which" WeekPlan it is.
- `MealPlan` has identity. Even if two plans have identical content, they're different plans with different histories. The UID matters.

This distinction seems academic until you implement equality checks and persistence. Getting it right early saves pain later.

**The Distribution Algorithm (`core/planning/operations/distribution.py`):**

This is the most interesting code in the app. I wanted to distribute dishes across weeks while maximizing variety:

```python
# core/planning/operations/distribution.py:44-66

def _score_dish(
    dish: Dish,
    state: _WeekState,
    recently_used: set[str],
) -> float:
    """Score a dish for selection. Higher is better."""
    score = 0.0

    # Reward new food categories
    new_categories = set(dish.categories) - state.categories_used
    score += len(new_categories) * 1.0

    # Reward cuisine novelty (within this week)
    if dish.cuisine not in state.cuisines_used:
        score += 0.5

    # Penalize recently-used dishes (spacing)
    if dish.uid in recently_used:
        score -= 1.0

    return score
```

**Why greedy instead of global optimization?**

I considered constraint satisfaction or integer linear programming for "optimal" distribution. But:

1. Greedy is fast and predictable
2. Users don't need optimal - they need "pretty good"
3. I can explain why a dish was chosen; can't explain ILP solutions easily
4. The algorithm runs on every "Generate Plan" click; speed matters

The greedy approach: for each week, pick the highest-scoring available dish, update state, repeat. Simple, fast, good enough.

### Context (User Preferences)

This context stores user preferences as natural language:

```python
# core/context/models.py:18-40

class UserContext(BaseModel):
    """A piece of user context/preference."""

    model_config = ConfigDict(frozen=True)

    uid: str = Field(default_factory=_context_uid)
    category: str | None = None  # "dietary", "location", etc.
    context: str = ""  # Natural language: "Vegetarian, no eggs"
```

**Why natural language instead of structured fields?**

I built this for AI integration. Structured fields like `is_vegetarian: bool` would require me to enumerate every possible preference. Natural language lets users express anything: "No eggs, prefer spicy food, cooking for 2 adults and a picky toddler."

The `Preferences.all_text()` method formats this for AI prompts. Yes, this means the domain knows about AI consumption - a smell I'll address in "What I'd Do Differently."

### Shared Types

I implemented Rust-style `Result` types for error handling:

```python
# core/shared/types.py:17-76

@dataclass(frozen=True)
class Ok(Generic[T]):
    """Success case."""
    value: T

    def is_ok(self) -> bool:
        return True

    def unwrap(self) -> T:
        return self.value

    def map(self, fn: Callable[[T], U]) -> "Result[U, Any]":
        return Ok(fn(self.value))


@dataclass(frozen=True)
class Err(Generic[E]):
    """Error case."""
    error: E

    def is_ok(self) -> bool:
        return False

    def unwrap(self) -> NoReturn:
        raise ValueError(f"Called unwrap on Err: {self.error}")


Result = Ok[T] | Err[E]
```

**Why this over exceptions?**

Exceptions are invisible in type signatures. A function that might fail looks identical to one that can't. With `Result[Dish, NotFoundError]`, the possibility of failure is explicit in the return type.

The trade-off: more verbose calling code. Instead of try/except, you do:

```python
result = catalogue.get_dish(uid)
if result.is_ok():
    dish = result.unwrap()
else:
    return Err(result.error)
```

I find this verbosity worthwhile for critical paths. For convenience methods, I sometimes still raise exceptions.

---

## The Services Layer

Services live in `meal_planning/services/`. They orchestrate domain objects and handle persistence.

### The Pattern

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SERVICES                                        │
│                                                                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│   │ Catalogue   │    │  Planning   │    │   Context   │                    │
│   │  Service    │    │   Service   │    │   Service   │                    │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                    │
│          │                  │                  │                            │
│          └──────────────────┼──────────────────┘                            │
│                             │                                               │
│                             ▼                                               │
│                    ┌─────────────────┐                                      │
│                    │    BlobStore    │  ← Port (Protocol)                   │
│                    │    (Protocol)   │                                      │
│                    └────────┬────────┘                                      │
│                             │                                               │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INFRASTRUCTURE                                     │
│                                                                             │
│                    ┌─────────────────┐                                      │
│                    │ LocalFilesystem │  ← Adapter (Implementation)          │
│                    │   BlobStore     │                                      │
│                    └─────────────────┘                                      │
│                                                                             │
│              (Could also be: S3BlobStore, GCSBlobStore, etc.)               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Port Abstractions

The `BlobStore` protocol is intentionally minimal:

```python
# services/ports/blobstore.py:15-48

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
```

**Why bytes, not dicts?**

I see many projects where the "storage abstraction" takes dictionaries and does JSON encoding internally. This couples you to JSON. What if you want Parquet for analytics? What if you want MessagePack for speed?

By making the port byte-oriented, serialization becomes the service's responsibility. The storage layer just moves bytes around. This makes it trivial to add new storage backends - they all speak the same language (bytes).

### Service Example: CatalogueService

```python
# services/catalogue.py:24-72

class CatalogueService:
    """Service for managing the dish catalogue."""

    def __init__(self, store: BlobStore, user_id: str = "default"):
        self._store = store
        self._user_id = user_id
        self._dishes: dict[str, Dish] = {}
        self._loaded = False

    def _key(self, filename: str) -> str:
        """Construct blob key with user scoping."""
        return f"{self._user_id}/{filename}"

    def _ensure_loaded(self) -> None:
        """Lazy load data from store."""
        if self._loaded:
            return

        dish_bytes = self._store.load_blob(self._key("dishes.json"))
        if dish_bytes:
            dish_data = json.loads(dish_bytes.decode("utf-8"))
            self._dishes = {
                uid: Dish.model_validate(data)
                for uid, data in dish_data.items()
            }
        self._loaded = True

    def add_dish(self, dish: Dish) -> Result[Dish, DuplicateError]:
        """Add a dish to the catalogue."""
        self._ensure_loaded()
        if dish.uid in self._dishes:
            return Err(DuplicateError("Dish", dish.uid))
        self._dishes[dish.uid] = dish
        return Ok(dish)

    def save(self) -> None:
        """Persist current state to storage."""
        data = {uid: dish.model_dump() for uid, dish in self._dishes.items()}
        self._store.save_blob(
            self._key("dishes.json"),
            json.dumps(data, indent=2).encode("utf-8")
        )
```

**Key patterns here:**

1. **Constructor injection**: `BlobStore` is injected, not created internally
2. **Lazy loading**: `_ensure_loaded()` defers disk I/O until needed
3. **User scoping**: `_key()` prefixes all paths with user_id for multi-user support
4. **Explicit save**: `save()` must be called manually (more on this inconsistency later)

### Orchestrating Services

Some services compose others without touching infrastructure:

```python
# services/analysis.py:25-61

class AnalysisService:
    """Orchestrates analysis across catalogue and planning."""

    def __init__(
        self,
        catalogue: "CatalogueService",
        planning: "PlanningService",
    ):
        self._catalogue = catalogue
        self._planning = planning

    def get_variety_report(self, plan_uid: str) -> Result[VarietyReport, NotFoundError]:
        """Analyze variety in a meal plan."""
        plan_result = self._planning.get_plan(plan_uid)
        if not plan_result.is_ok():
            return Err(plan_result.error)

        plan = plan_result.unwrap()
        dishes = self._catalogue.list_dishes()
        dish_map = {d.uid: d for d in dishes}

        return Ok(assess_variety(plan, dish_map))
```

`AnalysisService` doesn't touch `BlobStore` at all. It composes `CatalogueService` and `PlanningService`. This is composition over inheritance - no complex class hierarchies, just objects that use other objects.

---

## Dependency Injection & Wiring

All the wiring happens in `meal_planning/app.py`:

```python
# app.py:28-36

@dataclass
class AppContext:
    """Application context containing all services."""

    catalogue: CatalogueService
    planning: PlanningService
    context: ContextService
    analysis: AnalysisService
    ai_assistant: AIAssistantService
```

**Why a dataclass, not a DI framework?**

I considered `dependency-injector` or similar libraries. But for an app this size, a simple dataclass is clearer. Everyone can read this code without learning a framework's magic.

```python
# app.py:43-89

def create_app_context(
    data_path: Path | None = None,
    user_id: str | None = None,
    ai_client: "AIClientPort | None" = None,
) -> AppContext:
    """Create application context with all services wired up."""
    data_path = data_path or get_data_path()
    user_id = user_id or get_user_id()

    # Create infrastructure adapters
    store = LocalFilesystemBlobStore(data_path)

    # Create services with injected adapters
    catalogue = CatalogueService(store, user_id)
    planning = PlanningService(store, user_id)
    context = ContextService(store, user_id)

    # Create orchestrating services
    analysis = AnalysisService(catalogue, planning)
    ai_assistant = AIAssistantService(catalogue, planning, context, ai_client)

    return AppContext(
        catalogue=catalogue,
        planning=planning,
        context=context,
        analysis=analysis,
        ai_assistant=ai_assistant,
    )
```

The wiring is explicit. You can trace exactly which service gets which dependencies. No magic, no annotations, no runtime introspection.

---

## Patterns I Used (and Why)

### Immutability

Every domain model uses `frozen=True`:

```python
class Dish(BaseModel):
    model_config = ConfigDict(frozen=True)
    # ...
```

**Why?**

Consider this bug with mutable models:

```python
# BUG: Mutable model
dish = catalogue.get_dish("DISH-123")
dish.name = "New Name"  # This modifies the catalogue's internal copy!
# Now the catalogue has inconsistent state
```

With immutable models, you literally can't do this:

```python
# SAFE: Immutable model
dish = catalogue.get_dish("DISH-123")
dish.name = "New Name"  # TypeError: "Dish" is immutable
```

To modify, you must use builder methods that return new instances:

```python
# Explicit mutation via builder
new_dish = dish.with_category(Category.GREENS)
catalogue.update_dish(new_dish)
```

The mutation is visible in the code. No hidden side effects.

### Builder Methods

Since models are immutable, I provide "with_*" methods for modifications:

```python
# core/catalogue/models.py:65-93

def with_category(self, category: Category) -> "Dish":
    """Return new Dish with category added."""
    if category in self.categories:
        return self
    return Dish(
        uid=self.uid,
        name=self.name,
        categories=self.categories + (category,),
        cuisine=self.cuisine,
        tags=self.tags,
        recipe_reference=self.recipe_reference,
    )

def without_category(self, category: Category) -> "Dish":
    """Return new Dish with category removed."""
    return Dish(
        uid=self.uid,
        name=self.name,
        categories=tuple(c for c in self.categories if c != category),
        cuisine=self.cuisine,
        tags=self.tags,
        recipe_reference=self.recipe_reference,
    )
```

Yes, this is verbose. The alternative (mutable models) is worse.

### Lazy Loading

Services don't load data until needed:

```python
def _ensure_loaded(self) -> None:
    if self._loaded:
        return
    # ... load from disk
    self._loaded = True
```

**Why?**

Creating an `AppContext` is cheap - it just wires up services. The expensive disk I/O only happens when you actually call a method that needs data.

**The trade-off:** First access is slow. But subsequent accesses hit the in-memory cache. For a web app where the context persists across requests (via `AppContextManager`), this is the right trade-off.

### Pure Functions for Algorithms

The distribution algorithm is a pure function:

```python
# core/planning/operations/distribution.py:92-196

def distribute_dishes(
    dishes: list[Dish],
    num_weeks: int = 4,
    dishes_per_week: int = 4,
    eastern_per_week: int = 2,
    western_per_week: int = 2,
) -> DistributionResult:
    """Distribute dishes across weeks, maximizing variety."""
    # ... 100 lines of pure computation
    return DistributionResult(weeks=weeks, discarded=discarded, reused=reused)
```

Same input → same output. No side effects. No state modification.

**Testing is trivial:**

```python
def test_distribution_respects_regional_balance():
    dishes = [create_dish(cuisine=c) for c in Cuisine]
    result = distribute_dishes(dishes, num_weeks=1, dishes_per_week=4)
    week = result.weeks[0]

    eastern = sum(1 for uid in week.dishes if get_dish(uid).region == Region.EASTERN)
    western = sum(1 for uid in week.dishes if get_dish(uid).region == Region.WESTERN)

    assert eastern == 2
    assert western == 2
```

No mocking, no setup, no teardown. Just call the function with inputs and check outputs.

---

## Mistakes I Avoided

### The "Repository" Pattern Trap

Many DDD tutorials push you toward repository classes:

```python
# Over-engineered approach I avoided
class DishRepository:
    def find_by_id(self, id: str) -> Dish: ...
    def find_by_cuisine(self, cuisine: Cuisine) -> list[Dish]: ...
    def find_by_category(self, category: Category) -> list[Dish]: ...
    def save(self, dish: Dish) -> None: ...
    def delete(self, id: str) -> None: ...

class SqlDishRepository(DishRepository): ...
class MongoDishRepository(DishRepository): ...
class FileDishRepository(DishRepository): ...
```

This is massive overkill for a meal planner. I have one storage backend (filesystem) and don't need query flexibility.

**What I did instead:** Simple `BlobStore` for bytes in/out, services handle JSON encoding. If I ever need complex queries, I'll add DuckDB for analytics.

### The ORM Trap

I spent way too long debating whether to use SQLAlchemy. The allure of "proper" persistence was strong. But then I asked myself: what problem am I actually solving?

For a meal planner that resets on deploy anyway, JSON files are not just "good enough" - they're better:

- No migrations
- No connection pooling
- No ORM quirks (N+1 queries, lazy loading surprises)
- Human-readable data files
- Git-friendly diffs

Sometimes the boring choice is the right choice.

### Premature Abstraction

Things I considered adding but didn't:

- **Event bus**: For decoupling services. But I have 5 services that rarely interact. Not worth it.
- **Command/Query separation (CQRS)**: Overkill for read-heavy, low-write app.
- **Unit of Work pattern**: For transactional consistency. But JSON files don't need transactions.
- **Specification pattern**: For complex queries. But I don't have complex queries.

Each of these patterns has its place. That place is not a personal meal planning app.

---

## What I'd Do Differently

### The `Preferences.all_text()` Smell

```python
# core/context/aggregate.py:50-71

def all_text(self) -> str:
    """Format all contexts for AI prompts."""
    by_category: dict[str, list[str]] = {}
    for ctx in self._contexts.values():
        category = ctx.category or "general"
        by_category.setdefault(category, []).append(ctx.context)

    lines = []
    for category, contexts in by_category.items():
        lines.append(f"{category.title()}: {', '.join(contexts)}")
    return "\n".join(lines)
```

**The problem:** The domain layer knows it's being consumed by AI. This is a leaky abstraction.

**How I'd fix it:** Move `all_text()` to a formatter in the services layer:

```python
# Better: services/formatters.py
def format_preferences_for_ai(preferences: Preferences) -> str:
    """Format preferences for AI prompts."""
    # ... formatting logic
```

The domain stays pure; formatting is a presentation concern.

### Service Auto-Save Inconsistency

`PlanningService` auto-saves after mutations:

```python
def add_to_shortlist(self, dish_uid: str) -> Shortlist:
    self._shortlist = self._shortlist.add(dish_uid)
    self._save()  # Auto-save!
    return self._shortlist
```

`CatalogueService` requires explicit save:

```python
def add_dish(self, dish: Dish) -> Result[Dish, DuplicateError]:
    self._dishes[dish.uid] = dish
    return Ok(dish)
    # No auto-save! Caller must call save() explicitly
```

**The problem:** Inconsistent API. Sometimes you need to call `save()`, sometimes you don't. Easy to forget.

**How I'd fix it:** Pick one approach and apply it everywhere. I'd probably go with explicit save for everything - it's more predictable.

### The "default" User Leaking

```python
def __init__(self, store: BlobStore, user_id: str = "default"):
    self._user_id = user_id
```

**The problem:** `"default"` appears in multiple places as a magic string. It's easy to typo as `"Default"` or `"defaults"`.

**How I'd fix it:** Make `user_id` required (no default), and define the constant once:

```python
# config.py
DEFAULT_USER_ID = "default"

# usage
CatalogueService(store, user_id=config.DEFAULT_USER_ID)
```

Or better: make the CLI explicitly pass `"default"` so there's no magic at all.

---

## Longlist of Things to Do

### Code Cleanup

- [ ] **Make all services consistent on save behavior** - Either all auto-save or none do
- [ ] **Extract `Preferences.all_text()` to a formatter** - Domain shouldn't know about AI
- [ ] **Add more Result types** - Currently only some methods return `Result`, others raise. Should be consistent.
- [ ] **Make user_id non-optional** - Remove magic "default" strings

### Architecture Enhancements

- [ ] **Event sourcing for meal plan history** - Track what plans were generated, when, with what dishes
- [ ] **Undo/redo via command pattern** - Would be nice for "oops, removed wrong dish"
- [ ] **Caching layer** - If performance becomes an issue, add caching between services and BlobStore

### Testing

- [ ] **Property-based tests for distribution algorithm** - Use Hypothesis to find edge cases
- [ ] **Fuzzing for category/cuisine combinations** - What happens with 100 dishes all same cuisine?
- [ ] **Integration tests with real filesystem** - Currently relying on manual testing

### Documentation

- [ ] **Add ADR (Architecture Decision Records)** - Capture why key decisions were made
- [ ] **Sequence diagrams for complex flows** - Especially AI assistant conversation flow

---

## See Also

- [Web Architecture](web-architecture.md) - Dash UI layer
- [Session Architecture](session-architecture.md) - Multi-user support
- [BlobStore Concepts](blobstore101.md) - How storage works
