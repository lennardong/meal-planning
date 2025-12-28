# Meal Planning System

> A KISS (Keep It Simple, Stupid) meal planning application following Clean Architecture, Ports & Adapters, and functional programming practices.

## Table of Contents

- [Introduction: Why This Architecture?](#introduction-why-this-architecture)
- [Quick Start](#quick-start)
- [Technologies](#technologies)
- [Architecture Overview](#architecture-overview)
- [The Four Layers](#the-four-layers)
- [Key Patterns Explained](#key-patterns-explained)
- [Data Flow Diagrams](#data-flow-diagrams)
- [CLI Reference](#cli-reference)
- [Extending the System](#extending-the-system)

---

## Introduction: Why This Architecture?

Hey there! Let me walk you through why we built this system the way we did. I've been building systems at scale for a while, and the biggest lesson I've learned is this: **the best architecture is the one you can understand, modify, and extend without fear**.

### The Problem We're Solving

You want to plan meals for a month, generate shopping lists, and maybe have an AI help suggest dishes. Simple enough, right? But here's the thing—simple requirements have a way of growing. Today it's meal planning; tomorrow it's nutritional tracking, recipe scaling, or integration with grocery delivery services.

So we need an architecture that:
1. **Starts simple** - No over-engineering. A local filesystem is fine.
2. **Stays flexible** - When you need S3 or MongoDB, you can swap it in.
3. **Remains understandable** - Any engineer should grok it in an hour.

### The Solution: Clean Architecture + Ports & Adapters + Functional Core

We borrowed three big ideas:

1. **From Clean Architecture**: Layers with clear dependencies (core → services → infra)
2. **From Ports & Adapters**: Abstractions (ports) that infrastructure implements (adapters)
3. **From Functional Programming**: Immutable models, pure functions, explicit error handling

The result? A system where:
- Your domain logic (ingredients, dishes, plans) knows nothing about JSON or databases
- Storage is just bytes—swap filesystem for S3 by changing one adapter
- Everything is immutable, so no spooky action at a distance

---

## Quick Start

### Web UI (Palate)

```bash
# Development (hot reload on port 8051)
./devops/scripts/dev.sh

# Production (Docker on port 8050)
docker build -f devops/docker/Dockerfile.dash-app -t palate-dash-app .
docker run -d -p 8050:8060 --name palate-app palate-dash-app
```

Open http://localhost:8051 (dev) or http://localhost:8050 (Docker).

### CLI

```bash
# Install dependencies
uv sync

# Seed with sample data
uv run meal seed

# List dishes in catalogue
uv run meal catalogue list dishes

# Schedule a dish
uv run meal plan schedule 2025-01 --week 1 --day Mon --dish "Kimchee Fried Rice"

# View the plan
uv run meal plan show 2025-01

# Generate shopping list
uv run meal shop list 2025-01 --week 1
```

---

## Technologies

Let me walk you through the technology choices. Each library was selected deliberately—not because it's trendy, but because it solves a specific problem better than the alternatives.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DEPENDENCY GRAPH                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                              ┌─────────┐                                    │
│                              │   CLI   │                                    │
│                              └────┬────┘                                    │
│                                   │                                         │
│                    ┌──────────────┼──────────────┐                         │
│                    │              │              │                         │
│                    ▼              ▼              ▼                         │
│              ┌─────────┐   ┌─────────┐   ┌─────────────┐                   │
│              │  Typer  │   │  Rich   │   │  Pydantic   │                   │
│              │  (CLI   │   │ (Output │   │  (Domain    │                   │
│              │  Parser)│   │ Render) │   │   Models)   │                   │
│              └─────────┘   └─────────┘   └─────────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Package | Version | Layer | Purpose |
|---------|---------|-------|---------|
| **Pydantic** | >=2.12.5 | Core | Data validation, serialization, immutable models |
| **Typer** | >=0.9.0 | API/CLI | Command-line interface framework |
| **Rich** | >=13.0.0 | API/CLI | Terminal formatting, tables, colors |
| **Dash** | >=2.18 | API/Web | Reactive web framework |
| **Dash Mantine** | >=0.14 | API/Web | Mantine UI components for Dash |
| **Plotly** | >=5.24 | API/Web | Interactive charts |

---

## Architecture Overview

Let me draw you a picture. Here's how all the pieces fit together:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
│  meal catalogue add-ingredient, meal plan schedule, meal shop list          │
│                                                                             │
│  api/cli/main.py + api/cli/commands/*.py                                   │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SERVICES LAYER                                     │
│  CatalogueService, PlanningService, ShoppingService, AnalysisService        │
│                                                                             │
│  services/*.py + services/ports/*.py (BlobStore, AIClientPort)             │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           │                         │                         │
           ▼                         ▼                         ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   CORE/CATALOGUE │    │  CORE/PLANNING   │    │   CORE/CONTEXT   │
│   (Pure Domain)  │    │  (Pure Domain)   │    │   (Pure Domain)  │
├──────────────────┤    ├──────────────────┤    ├──────────────────┤
│ models.py        │    │ models.py        │    │ models.py        │
│  - VOIngredient  │    │  - MonthlyPlan   │    │  - VOUserContext │
│  - VODish        │    │  - WeekPlan      │    │                  │
│                  │    │                  │    │                  │
│ enums.py         │    │ enums.py         │    │                  │
│  - PurchaseType  │    │  - Day           │    │                  │
│  - IngredientTag │    │                  │    │                  │
│  - DishTag       │    │ operations/      │    │                  │
│                  │    │  - shopping.py   │    │                  │
│                  │    │  - analysis.py   │    │                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
           │                         │                         │
           └─────────────────────────┼─────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            INFRA LAYER                                       │
│  LocalFilesystemBlobStore, ClaudeClient, migration utilities                │
│                                                                             │
│  infra/stores/*.py, infra/ai/*.py, infra/config/*.py                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
                   ┌─────────────────────────────────────┐
                   │           data/{user_id}/           │
                   │  ingredients.json  dishes.json      │
                   │  plans.json        contexts.json    │
                   └─────────────────────────────────────┘
```

### Why This Layering?

Think of it like a good restaurant:
- **API** is the waiter—takes orders, presents food, handles customer interaction
- **Services** is the head chef—coordinates everything, knows who does what
- **Core** is the recipe book—pure knowledge, no kitchen equipment
- **Infra** is the kitchen equipment—ovens, fridges, but easily replaceable

The key insight: **dependencies point inward**. Core knows nothing about Services. Services know nothing about API or Infra. This is what makes the system flexible.

---

## The Four Layers

### 1. Core Layer (`core/`)

**Purpose**: Pure domain models and operations. ZERO I/O.

This is the heart of your application. It contains:
- **Models**: Immutable Pydantic classes (`VOIngredient`, `VODish`, `MonthlyPlan`)
- **Enums**: Domain vocabularies (`PurchaseType`, `Day`, `DishTag`)
- **Operations**: Pure functions that compute without side effects
- **Shared Types**: `Result`, `Ok`, `Err` for functional error handling

```
core/
├── catalogue/
│   ├── models.py      # VOIngredient, VODish
│   └── enums.py       # PurchaseType, IngredientTag, DishTag
├── planning/
│   ├── models.py      # MonthlyPlan, WeekPlan
│   ├── enums.py       # Day
│   └── operations/    # Pure functions!
│       ├── shopping.py    # generate_shopping_list()
│       └── analysis.py    # assess_variety()
├── context/
│   └── models.py      # VOUserContext
└── shared/
    └── types.py       # Result, Ok, Err, NotFoundError, DuplicateError
```

**Key Insight**: Everything in `core/` is testable without mocks. Pure functions, immutable data.

```python
# core/catalogue/models.py
class VOIngredient(BaseModel):
    model_config = ConfigDict(frozen=True)  # Immutable!

    uid: str = Field(default_factory=_ingredient_uid)
    name: str
    tags: tuple[IngredientTag, ...] = Field(default_factory=tuple)
    purchase_type: PurchaseType = PurchaseType.WEEKLY
```

### 2. Services Layer (`services/`)

**Purpose**: Application orchestration + Port definitions.

Services handle:
- **Orchestration**: Coordinate multiple domain operations
- **Serialization**: JSON encoding/decoding (the domain doesn't know about JSON)
- **Key Construction**: Build storage keys like `{user_id}/ingredients.json`
- **Port Definitions**: Interfaces that infrastructure must implement

```
services/
├── ports/
│   ├── blobstore.py   # BlobStore protocol (bytes in/out)
│   └── ai_client.py   # AIClientPort protocol
├── catalogue.py       # CatalogueService (JSON + key construction)
├── planning.py        # PlanningService
├── context.py         # ContextService
├── shopping.py        # ShoppingService (uses core operations)
├── analysis.py        # AnalysisService
└── ai_assistant.py    # AIAssistantService
```

**The BlobStore Port** (this is key!):

```python
# services/ports/blobstore.py
class BlobStore(Protocol):
    """Low-level blob storage. Format-agnostic, domain-agnostic."""

    def save_blob(self, key: str, data: bytes) -> None: ...
    def load_blob(self, key: str) -> bytes | None: ...
    def delete_blob(self, key: str) -> None: ...
    def list_blobs(self, prefix: str = "") -> list[str]: ...
```

**Why bytes, not dicts?** The BlobStore doesn't know or care about JSON. It just moves bytes. This means:
- Same interface for JSON, Parquet, images, anything
- Swap LocalFilesystem → S3 → Azure without changing services
- Services own serialization decisions

**Services Handle JSON + Keys**:

```python
# services/catalogue.py
class CatalogueService:
    def __init__(self, store: BlobStore, user_id: str = "default"):
        self._store = store
        self._user_id = user_id

    def _key(self, filename: str) -> str:
        return f"{self._user_id}/{filename}"  # e.g., "default/ingredients.json"

    def save(self) -> None:
        data = {uid: ing.model_dump() for uid, ing in self._ingredients.items()}
        self._store.save_blob(
            self._key("ingredients.json"),
            json.dumps(data, indent=2).encode("utf-8")  # Service does JSON!
        )
```

### 3. Infrastructure Layer (`infra/`)

**Purpose**: Implement ports with concrete adapters.

This is where I/O lives. All the "dirty" stuff—filesystems, APIs, databases—goes here.

```
infra/
├── stores/
│   ├── local_filesystem.py   # LocalFilesystemBlobStore
│   └── migration.py          # Auto-migrate old format
├── ai/
│   ├── claude_client.py      # ClaudeClient implements AIClientPort
│   └── prompts.py            # Prompt templates
└── config/
    └── settings.py           # Paths, defaults
```

**The LocalFilesystemBlobStore**:

```python
# infra/stores/local_filesystem.py
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

**Future Adapters** (same interface!):
- `S3BlobStore` - Amazon S3
- `GCSBlobStore` - Google Cloud Storage
- `MemoryBlobStore` - For testing

### 4. API Layer (`api/`)

**Purpose**: External interfaces. CLI for power users, Web UI for visual meal planning.

```
api/
├── cli/                       # Command-line interface
│   ├── main.py                # Typer app with nested subcommands
│   └── commands/
│       ├── catalogue.py       # meal catalogue add-ingredient/list
│       ├── planning.py        # meal plan show/schedule
│       ├── shopping.py        # meal shop list
│       ├── analysis.py        # meal analysis variety
│       └── context.py         # meal context add/list
│
└── dash/                      # Web UI (Palate)
    ├── app.py                 # Dash app, layout, MantineProvider
    ├── callbacks.py           # Reactive callbacks
    ├── components.py          # Component factories
    └── assets/style.css       # Design system (CSS variables)
```

**Web UI Architecture** (see `api/dash/README.md` for details):
- **Kanban-style** two-column layout (Catalogue ↔ Shortlist)
- **Mantine components** with custom theme (saffron palette)
- **CSS variables** injected from `theme.py` for consistent colors
- **Plotly charts** for diversity analysis

**Nested Commands**:

```bash
meal catalogue add-ingredient "Rice" --bulk
meal catalogue list dishes
meal plan show 2025-01
meal plan schedule 2025-01 --week 1 --day Mon --dish "Fried Rice"
meal shop list 2025-01 --week 1
meal analysis variety 2025-01
meal context add "Vegetarian" --category dietary
```

### 5. Presentation Layer (`theme.py`)

**Purpose**: Single source of truth for all presentation tokens. Keeps core domain pure.

```python
# theme.py
CUISINE_FLAG: dict[Cuisine, str] = {
    Cuisine.KOREAN: "🇰🇷",
    Cuisine.JAPANESE: "🇯🇵",
    ...
}

CATEGORY_COLOR: dict[Category, CategoryColor] = {
    Category.GREENS: CategoryColor("#E8F5E9", "#3D6B4A"),
    ...
}

def generate_category_css_vars() -> str:
    """Inject CSS variables into HTML head."""
    ...
```

**Why separate?** Colors and flags are presentation concerns, not domain logic. By keeping them in `theme.py`:
- Core domain stays pure (no presentation knowledge)
- Single source of truth for both CSS and Plotly charts
- Easy to update colors without touching domain code

### 6. Bootstrap (`app.py`)

**Purpose**: Wire everything together. Dependency injection happens here.

```python
# app.py
def create_app_context(
    data_path: Path | None = None,
    user_id: str | None = None,
    ai_client: AIClientPort | None = None,
) -> AppContext:
    # Auto-migrate if needed
    migrate_if_needed(data_path, user_id)

    # Create adapter
    store = LocalFilesystemBlobStore(data_path)

    # Create services with injected adapter
    catalogue = CatalogueService(store, user_id)
    planning = PlanningService(store, user_id)
    context = ContextService(store, user_id)

    # Create orchestrating services
    shopping = ShoppingService(catalogue, planning)
    analysis = AnalysisService(catalogue, planning)
    ai_assistant = AIAssistantService(catalogue, planning, context, ai_client)

    return AppContext(catalogue, planning, context, shopping, analysis, ai_assistant)
```

---

## Key Patterns Explained

### 1. The BlobStore Pattern (Repository Decomposed)

**Problem**: You want to swap filesystem for S3 without rewriting your services.

**Solution**: Decompose the traditional Repository into two parts:
- **BlobStore**: Generic byte storage (infrastructure concern)
- **Service**: Domain mapping + serialization (application concern)

```
Traditional Repository = BlobStore + Service
                         (bytes)    (domain ↔ JSON)
```

**Why decompose?** The traditional Repository does two things: (1) store/retrieve data, and (2) map between domain objects and storage format. By splitting these, we get more flexibility—swap storage without touching serialization, or change JSON→Parquet without touching storage.

```python
# The port (in services/ports/)
class BlobStore(Protocol):
    def save_blob(self, key: str, data: bytes) -> None: ...
    def load_blob(self, key: str) -> bytes | None: ...

# The adapter (in infra/stores/)
class LocalFilesystemBlobStore:
    def save_blob(self, key: str, data: bytes) -> None:
        path = self.base_path / key
        path.write_bytes(data)

# Tomorrow: S3BlobStore, same interface
class S3BlobStore:
    def save_blob(self, key: str, data: bytes) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)
```

**Key Structure**:
```
data/
└── {user_id}/                    # Default: "default"
    ├── ingredients.json          # {"ING-xxx": {...}, ...}
    ├── dishes.json               # {"DISH-xxx": {...}, ...}
    ├── plans.json                # {"PLAN-2025-01": {...}, ...}
    └── contexts.json             # {"CTX-xxx": {...}, ...}
```

Why include `.json` in the key? Self-describing. Tools like DuckDB can infer format. Future: add `.parquet` files alongside.

### 2. Result Types (Functional Error Handling)

**Problem**: Exceptions are invisible. You don't know if a function can fail until it blows up.

**Solution**: Return `Result[T, E]` types that force you to handle errors.

```python
# Instead of:
def get(uid: str) -> VOIngredient:  # Might raise NotFoundError!
    ...

# We do:
def get_ingredient(self, uid: str) -> Result[VOIngredient, NotFoundError]:
    ing = self._ingredients.get(uid)
    if ing is None:
        return Err(NotFoundError("Ingredient", uid))
    return Ok(ing)
```

Now the caller **must** handle both cases:
```python
result = catalogue.get_ingredient("ING-123")
if result.is_ok():
    ingredient = result.unwrap()
else:
    print(f"Not found: {result.error}")
```

### 3. Immutable Models

**Problem**: Mutable state leads to bugs. Someone modifies an object, and suddenly things break elsewhere.

**Solution**: `frozen=True` makes Pydantic models immutable.

```python
class VODish(BaseModel):
    model_config = ConfigDict(frozen=True)  # Immutable!

    uid: str
    name: str
    ingredient_uids: tuple[str, ...]  # tuple, not list!

# This fails:
dish.name = "New Name"  # FrozenInstanceError!

# This works:
new_dish = dish.model_copy(update={"name": "New Name"})
```

### 4. Pure Operations in Core

**Problem**: Business logic mixed with I/O is hard to test.

**Solution**: Put pure functions in `core/*/operations/`. They take data, return data, no side effects.

```python
# core/planning/operations/shopping.py
def generate_shopping_list(
    plan: MonthlyPlan,
    week_num: int,
    dishes: Sequence[VODish],
    ingredients: Sequence[VOIngredient],
) -> ShoppingList:
    # Pure function - no I/O, just computation
    # Same input = same output. Always.
    ...
```

Services call these with data they've loaded:
```python
# services/shopping.py
class ShoppingService:
    def get_weekly_list(self, month: str, week_num: int) -> ShoppingList | None:
        plan = self._planning.get_plan_for_month(month)
        dishes = self._catalogue.list_dishes()
        ingredients = self._catalogue.list_ingredients()

        # Call pure function
        return generate_shopping_list(plan, week_num, dishes, ingredients)
```

---

## Data Flow Diagrams

### Adding an Ingredient

```
User                CLI                 Service             BlobStore           Filesystem
 │                   │                    │                    │                    │
 │ meal catalogue    │                    │                    │                    │
 │ add-ingredient    │                    │                    │                    │
 │ "Rice" --bulk     │                    │                    │                    │
 │──────────────────>│                    │                    │                    │
 │                   │                    │                    │                    │
 │                   │ get_app_context()  │                    │                    │
 │                   │───────────────────>│                    │                    │
 │                   │                    │                    │                    │
 │                   │ add_ingredient()   │                    │                    │
 │                   │───────────────────>│                    │                    │
 │                   │                    │ (in-memory only)   │                    │
 │                   │                    │                    │                    │
 │                   │ save()             │                    │                    │
 │                   │───────────────────>│                    │                    │
 │                   │                    │ json.dumps()       │                    │
 │                   │                    │ .encode('utf-8')   │                    │
 │                   │                    │                    │                    │
 │                   │                    │ save_blob(         │                    │
 │                   │                    │   "default/        │                    │
 │                   │                    │   ingredients.json"│                    │
 │                   │                    │   bytes)           │                    │
 │                   │                    │───────────────────>│                    │
 │                   │                    │                    │ write_bytes()      │
 │                   │                    │                    │───────────────────>│
 │                   │                    │                    │                    │
 │ "Added: Rice"     │                    │                    │                    │
 │<──────────────────│                    │                    │                    │
```

### Generating a Shopping List

```
User                CLI                 ShoppingService      CatalogueService    Core Operations
 │                   │                    │                    │                    │
 │ meal shop list    │                    │                    │                    │
 │ 2025-01 --week 1  │                    │                    │                    │
 │──────────────────>│                    │                    │                    │
 │                   │                    │                    │                    │
 │                   │ get_weekly_list()  │                    │                    │
 │                   │───────────────────>│                    │                    │
 │                   │                    │                    │                    │
 │                   │                    │ get_plan()         │                    │
 │                   │                    │───────────────────>│                    │
 │                   │                    │<───────────────────│ MonthlyPlan        │
 │                   │                    │                    │                    │
 │                   │                    │ list_dishes()      │                    │
 │                   │                    │───────────────────>│                    │
 │                   │                    │<───────────────────│ [VODish, ...]      │
 │                   │                    │                    │                    │
 │                   │                    │ list_ingredients() │                    │
 │                   │                    │───────────────────>│                    │
 │                   │                    │<───────────────────│ [VOIngredient, ...]│
 │                   │                    │                    │                    │
 │                   │                    │ generate_shopping_list()               │
 │                   │                    │ (PURE FUNCTION - no I/O!)              │
 │                   │                    │───────────────────────────────────────>│
 │                   │                    │<───────────────────────────────────────│
 │                   │                    │                    │    ShoppingList    │
 │                   │<───────────────────│ ShoppingList       │                    │
 │                   │                    │                    │                    │
 │ Bulk: Rice        │                    │                    │                    │
 │ Weekly: Spinach   │                    │                    │                    │
 │<──────────────────│                    │                    │                    │
```

---

## CLI Reference

### Catalogue Commands

```bash
meal catalogue add-ingredient <name> [--tag TAG] [--bulk]
meal catalogue add-dish <name> [--tag TAG] [--ingredients "ing1,ing2"]
meal catalogue list [ingredients|dishes|all]
```

| Command | Description | Example |
|---------|-------------|---------|
| `add-ingredient` | Add ingredient | `meal catalogue add-ingredient "Rice" --tag Grain --bulk` |
| `add-dish` | Add dish | `meal catalogue add-dish "Fried Rice" --tag Eastern -i "Rice,Eggs"` |
| `list` | List items | `meal catalogue list dishes` |

### Planning Commands

```bash
meal plan show <month>
meal plan create <month>
meal plan schedule <month> --week N --day DAY [--dish NAME]
```

| Command | Description | Example |
|---------|-------------|---------|
| `show` | Display plan | `meal plan show 2025-01` |
| `create` | Create new plan | `meal plan create 2025-01` |
| `schedule` | Schedule dish | `meal plan schedule 2025-01 -w 1 -d Mon --dish "Fried Rice"` |

### Shopping Commands

```bash
meal shop list <month> [--week N]
```

| Command | Description | Example |
|---------|-------------|---------|
| `list` | Shopping list | `meal shop list 2025-01 --week 1` |
| `list` (monthly) | All ingredients | `meal shop list 2025-01` |

### Analysis Commands

```bash
meal analysis variety <month>
meal analysis suggest <month>
```

| Command | Description | Example |
|---------|-------------|---------|
| `variety` | Analyze variety | `meal analysis variety 2025-01` |
| `suggest` | Get suggestions | `meal analysis suggest 2025-01` |

### Context Commands

```bash
meal context add <text> [--category CAT]
meal context list
meal context delete <uid>
```

| Command | Description | Example |
|---------|-------------|---------|
| `add` | Add preference | `meal context add "Vegetarian" --category dietary` |
| `list` | List preferences | `meal context list` |
| `delete` | Remove preference | `meal context delete CTX-abc123` |

### Utility Commands

```bash
meal seed      # Load sample data
meal migrate   # Migrate old data format
meal status    # Show data status
```

---

## Extending the System

### Adding a New Storage Backend (e.g., S3)

1. Create `infra/stores/s3.py`:
```python
import boto3

class S3BlobStore:
    def __init__(self, bucket: str):
        self.bucket = bucket
        self.client = boto3.client('s3')

    def save_blob(self, key: str, data: bytes) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)

    def load_blob(self, key: str) -> bytes | None:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response['Body'].read()
        except self.client.exceptions.NoSuchKey:
            return None
```

2. Update `app.py`:
```python
# Instead of LocalFilesystemBlobStore
from infra.stores.s3 import S3BlobStore
store = S3BlobStore(bucket="my-meal-planning")
```

3. Services? **Unchanged**. Core? **Unchanged**. That's the beauty of ports and adapters.

### Adding a New Analysis Operation

1. Add pure function to `core/planning/operations/`:
```python
# core/planning/operations/nutrition.py
def assess_nutrition(
    plan: MonthlyPlan,
    dishes: Sequence[VODish],
    nutrition_data: dict[str, NutritionInfo],
) -> NutritionReport:
    # Pure function - compute nutritional analysis
    ...
```

2. Add service in `services/`:
```python
# services/nutrition.py
class NutritionService:
    def get_report(self, month: str) -> NutritionReport:
        plan = self._planning.get_plan_for_month(month)
        dishes = self._catalogue.list_dishes()
        return assess_nutrition(plan, dishes, self._nutrition_data)
```

3. Add CLI command:
```python
# api/cli/commands/analysis.py
@app.command("nutrition")
def nutrition(month: str):
    report = ctx.nutrition.get_report(month)
    console.print(format_report(report))
```

### Adding AI-Powered Suggestions

1. The port already exists (`services/ports/ai_client.py`)

2. Inject ClaudeClient in bootstrap:
```python
from infra.ai.claude_client import ClaudeClient

ai_client = ClaudeClient(api_key=os.environ["ANTHROPIC_API_KEY"])
ctx = create_app_context(ai_client=ai_client)
```

3. Use via `AIAssistantService`:
```python
suggestion = ctx.ai_assistant.suggest_plan("2025-01")
```

---

## Directory Structure Summary

```
meal_planning/
├── core/                           # DOMAIN - Pure models & operations (ZERO I/O)
│   ├── catalogue/
│   │   ├── models.py              # VOIngredient, VODish
│   │   └── enums.py               # PurchaseType, Category, Cuisine, Region
│   ├── planning/
│   │   ├── models.py              # MonthlyPlan, WeekPlan
│   │   ├── enums.py               # Day
│   │   └── operations/            # Pure functions
│   │       ├── shopping.py        # generate_shopping_list()
│   │       └── analysis.py        # assess_variety()
│   ├── context/
│   │   └── models.py              # VOUserContext
│   └── shared/
│       └── types.py               # Result, Ok, Err, errors
│
├── services/                       # APPLICATION - Ports + Orchestration
│   ├── ports/                     # Interfaces (what services NEED)
│   │   ├── blobstore.py           # BlobStore protocol (bytes)
│   │   └── ai_client.py           # AIClientPort protocol
│   ├── catalogue.py               # CatalogueService
│   ├── planning.py                # PlanningService
│   ├── context.py                 # ContextService
│   ├── shopping.py                # ShoppingService
│   ├── analysis.py                # AnalysisService
│   └── ai_assistant.py            # AIAssistantService
│
├── infra/                          # ADAPTERS - Implement ports
│   ├── stores/                    # Storage adapters
│   │   ├── local_filesystem.py    # LocalFilesystemBlobStore
│   │   └── migration.py           # Auto-migrate old format
│   ├── ai/                        # AI adapters
│   │   ├── claude_client.py       # ClaudeClient
│   │   └── prompts.py             # Prompt templates
│   └── config/
│       └── settings.py            # Paths, defaults
│
├── api/                            # EXTERNAL INTERFACES
│   ├── cli/                       # Command-line interface
│   │   ├── main.py                # Typer app with subcommands
│   │   └── commands/
│   │       ├── catalogue.py       # meal catalogue ...
│   │       ├── planning.py        # meal plan ...
│   │       ├── shopping.py        # meal shop ...
│   │       ├── analysis.py        # meal analysis ...
│   │       └── context.py         # meal context ...
│   │
│   └── dash/                      # Web UI (Palate)
│       ├── app.py                 # Dash app, layout, theme injection
│       ├── callbacks.py           # Reactive callbacks
│       ├── components.py          # Component factories
│       ├── assets/style.css       # Design system
│       └── README.md              # Dash architecture docs
│
├── theme.py                        # PRESENTATION - Colors, flags, CSS tokens
│
├── copy/                           # UI copy/content (markdown)
│   ├── app_header.md
│   ├── app_about.md
│   └── app_get_started.md
│
├── docs/
│   └── blobstore101.md            # BlobStore concepts guide
│
└── app.py                          # Bootstrap: wire adapters → services
```

---

## Final Thoughts

This architecture might seem like overkill for a meal planning app. But here's the thing: **it's not about the app, it's about the skills**.

By building this way, you've learned:
- How to separate concerns with clean layers
- How to use ports and adapters for flexible infrastructure
- How to keep domain logic pure and testable
- How to design for change without over-engineering

The BlobStore pattern is particularly powerful. Today it's a local filesystem. Tomorrow it's S3. Next week it's a distributed cache. Same services, same core—just swap the adapter.

These patterns scale. From a JSON file to a distributed system with message queues and event sourcing—the principles are the same.

Now go plan some meals.

---

*Built with love, following principles from Clean Architecture, Ports & Adapters, and decades of hard-won engineering wisdom.*
