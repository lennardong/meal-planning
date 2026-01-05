# Web Architecture: The Dash UI Layer

> How Palate presents itself to users - components, callbacks, state management, and styling.

## Table of Contents

- [Why Dash?](#why-dash)
- [Component Architecture](#component-architecture)
- [Callback Organization](#callback-organization)
- [State Management](#state-management)
- [Styling Approach](#styling-approach)
- [The "No JavaScript" Philosophy](#the-no-javascript-philosophy)
- [Mistakes I Made](#mistakes-i-made)
- [What I'd Do Differently](#what-id-do-differently)
- [Longlist of Things to Do](#longlist-of-things-to-do)

---

## Why Dash?

I evaluated several options for the web layer:

| Option | Considered | Verdict |
|--------|------------|---------|
| React + FastAPI | Yes | REJECTED |
| Vue + Flask | Briefly | REJECTED |
| Flask templates (Jinja) | Yes | REJECTED |
| Streamlit | Yes | REJECTED |
| **Dash + Mantine** | Yes | **CHOSEN** |

### The Decision

I went with Dash for one reason: **I wanted to stay in Python**.

I'm a decent Python developer and a mediocre JavaScript developer. React would mean:
- Learning (or relearning) React hooks, state management, build tooling
- Maintaining two codebases (Python backend + JS frontend)
- Debugging across language boundaries
- npm/yarn/pnpm dependency hell

Dash lets me write the entire app in Python. The trade-offs are real, but for a personal project, developer velocity matters more than architectural purity.

### What I Gave Up

Let me be honest about what Dash can't do well:

**No client-side routing.** Every navigation is a server round-trip. You can't do `palate.io/plan/123` - everything is query parameters or state.

**No component-level state.** In React, a component can manage its own state. In Dash, all state flows through callbacks to the server. This makes some patterns awkward.

**Limited NPM ecosystem.** Want to use that fancy React charting library? You'll need to wrap it as a Dash component or find a Dash-native alternative.

**Callback complexity at scale.** With 20+ callbacks, debugging "why did this fire?" becomes painful. Dash's reactive model is great until it isn't.

### What I Gained

**Pure Python.** One language, one debugger, one set of dependencies. When something breaks, I know how to fix it.

**Reactive callbacks are intuitive.** "When X changes, update Y" is a natural mental model. The callback decorator makes dependencies explicit.

**Mantine components are beautiful.** Dash Mantine Components gives me a professional-looking UI out of the box. No CSS framework hunting.

**Fast iteration.** Hot reload with `debug=True`. Change code, see results. No webpack rebuilds.

### The Honest Trade-off

**Dash is wrong for:** SPAs with complex client-side state, real-time collaborative features, offline-first apps, anything needing <50ms response times.

**Dash is right for:** Data dashboards, internal tools, personal projects where you value Python proficiency over frontend best practices.

I made a pragmatic choice. It's served me well for this project.

---

## Component Architecture

All components live in `api/dash/components.py`. I use a factory pattern - functions that return component trees.

### Factory Pattern

```python
# api/dash/components.py:63-90

def dish_card(dish: Dish, direction: str = "right") -> dmc.Card:
    """Create a dish card with actions.

    Args:
        dish: The dish to display
        direction: "right" to add to shortlist, "left" to remove
    """
    is_add = direction == "right"
    action_id = {"type": "add-dish" if is_add else "remove-dish", "uid": dish.uid}
    action_icon = IconArrowRight if is_add else IconArrowLeft

    return dmc.Card(
        className="card",
        children=[
            dmc.Group(
                className="card__header",
                children=[
                    html.Span(dish.name, className="card__title"),
                    html.Span(cuisine_flag(dish.cuisine), className="card__flag"),
                    dmc.ActionIcon(
                        action_icon(size=16),
                        id=action_id,
                        className="card__actions",
                        variant="subtle",
                    ),
                ],
            ),
            dmc.Group(
                className="card__tags",
                children=[category_tag(cat) for cat in dish.categories],
            ),
        ],
    )
```

**Why functions, not classes?**

React has class components and functional components. The React community moved toward functions because they're simpler. I followed that intuition.

Functions are:
- Easier to test (call with args, check output)
- Easier to compose (just call other functions)
- No `self` to manage
- No lifecycle methods to forget

**Composition over configuration:**

Notice the `direction` parameter. The same `dish_card()` function creates cards for both the catalogue (add to shortlist) and the shortlist (remove from shortlist). One component, two contexts.

```python
# In catalogue column
dish_card(dish, direction="right")  # Shows → icon, triggers add-dish

# In shortlist column
dish_card(dish, direction="left")   # Shows ← icon, triggers remove-dish
```

I could have made `CatalogueCard` and `ShortlistCard` as separate components. But they're 95% identical. Parameterization beats duplication.

### Data-Driven Styling

Instead of computed class names, I use data attributes:

```python
# api/dash/components.py:35-44

def category_tag(category: Category) -> html.Span:
    """Create a category tag with data-attribute for styling."""
    return html.Span(
        category.value.replace("_", " ").title(),
        className="tag--category",
        **{"data-category": category.value},  # CSS targets this
    )
```

```css
/* assets/style.css:296-305 */
.tag--category[data-category="greens"] {
    background-color: var(--cat-greens-bg);
    color: var(--cat-greens-text);
}

.tag--category[data-category="legumes"] {
    background-color: var(--cat-legumes-bg);
    color: var(--cat-legumes-text);
}
```

**Why not computed class names?**

The alternative is generating class names dynamically:

```python
# Alternative I avoided
className=f"tag--{category.value}"  # "tag--greens", "tag--legumes"
```

This works, but:
1. CSS must define every possible class
2. If you add a new category, you must add new CSS
3. Can't use CSS variable theming easily

With data attributes, the CSS uses selectors that match attribute values. The CSS is driven by data, not by knowing every possible value upfront.

### The Caching Problem

I made a mistake with module-level caching:

```python
# api/dash/components.py:47-60

_cached_dishes: list | None = None
_cached_cuisines: list | None = None

def _get_cached_data():
    """Cache dish data to avoid repeated service calls."""
    global _cached_dishes, _cached_cuisines

    if _cached_dishes is None:
        from meal_planning.app import get_app_context
        ctx = get_app_context()
        dishes = ctx.catalogue.list_dishes()
        _cached_dishes = dishes
        _cached_cuisines = sorted(set(d.cuisine.value for d in dishes))

    return _cached_dishes, _cached_cuisines
```

**The bug:** This cache is never invalidated. If a user adds or removes a dish, the dropdown options (which use this cache) show stale data until the server restarts.

**Why I did it:** The cuisine filter dropdown options don't change often. Loading all dishes on every dropdown render seemed wasteful.

**The lesson:** Premature optimization. The dropdown renders once per page load. Loading dishes takes milliseconds. I should have skipped the cache and added it only if profiling showed it mattered.

---

## Callback Organization

All callbacks live in `api/dash/callbacks.py` (604 lines). I organized them into logical sections:

```python
# api/dash/callbacks.py structure

# =============================================================================
# Session Management (lines 31-54)
# =============================================================================
# init_session() - Generate UUID on first visit
# update_shortlist_store() - Handle add/remove actions

# =============================================================================
# Rendering & Filtering (lines 83-122)
# =============================================================================
# render_columns() - Re-render both columns on filter/selection change

# =============================================================================
# Analysis Generation (lines 125-424)
# =============================================================================
# generate_plan() - THE BIG ONE: 270 lines

# =============================================================================
# CRUD & Modals (lines 431-603)
# =============================================================================
# open_modal() - Open dish modal for add/edit
# save_dish() - Save new or edited dish
# delete_dish() - Delete dish
# toggle_info_modal() - About modal
# toggle_get_started_modal() - Help modal
```

### Pattern-Matching Callbacks

Dash's pattern-matching callbacks are powerful. Instead of registering a callback for each dish card:

```python
# Tedious approach I avoided
@callback(..., Input("add-dish-DISH-001", "n_clicks"))
@callback(..., Input("add-dish-DISH-002", "n_clicks"))
@callback(..., Input("add-dish-DISH-003", "n_clicks"))
# ... for every dish
```

I use dynamic IDs with `ALL`:

```python
# api/dash/callbacks.py:56-80

@callback(
    Output("shortlist-store", "data"),
    Input({"type": "add-dish", "uid": ALL}, "n_clicks"),
    Input({"type": "remove-dish", "uid": ALL}, "n_clicks"),
    State("shortlist-store", "data"),
    prevent_initial_call=True,
)
def update_shortlist_store(add_clicks, remove_clicks, current_shortlist):
    """Handle add/remove dish actions via pattern-matching callbacks."""
    triggered = ctx.triggered_id
    if not triggered or not isinstance(triggered, dict):
        return current_shortlist

    uid = triggered.get("uid")
    action = triggered.get("type")

    if action == "add-dish" and uid not in current_shortlist:
        return current_shortlist + [uid]
    elif action == "remove-dish" and uid in current_shortlist:
        return [u for u in current_shortlist if u != uid]

    return current_shortlist
```

**How it works:**

1. Button IDs are dicts: `{"type": "add-dish", "uid": "DISH-123"}`
2. `Input({"type": "add-dish", "uid": ALL}, ...)` matches all buttons where `type == "add-dish"`
3. `ctx.triggered_id` tells you which specific button was clicked
4. You extract the UID from the triggered ID

**When to use pattern-matching:**

- Lists of similar items (dishes, cards, rows)
- Dynamic content where count isn't known at design time

**When to use explicit IDs:**

- Singular elements (the "Generate Plan" button)
- Elements with distinct behaviors (different modals)

### The `_get_context()` Helper

Every data-touching callback needs the user's session:

```python
# api/dash/callbacks.py:19-23

def _get_context(session_id: str | None):
    """Get app context for session, falling back to default."""
    if session_id:
        return get_user_context(session_id)
    return get_app_context()
```

This is the integration point between web and app architecture. The callback receives `session_id` from the Store, passes it to `_get_context()`, and gets back a user-scoped `AppContext`.

**The pattern in every callback:**

```python
@callback(
    Output(...),
    Input(...),
    State("session-id-store", "data"),  # Always include this
)
def my_callback(..., session_id):
    app_ctx = _get_context(session_id)  # Always first line
    # Now use app_ctx.catalogue, app_ctx.planning, etc.
```

See [Session Architecture](session-architecture.md) for the full multi-user story.

### Common Callback Patterns

**PreventUpdate guards:**

```python
# api/dash/callbacks.py:451-453

if not ctx.triggered or ctx.triggered[0]["value"] is None:
    raise PreventUpdate
```

Callbacks fire on page load with `None` values. This guard prevents processing empty triggers.

**allow_duplicate outputs:**

```python
# api/dash/callbacks.py:502

Output("dish-modal", "opened", allow_duplicate=True)
```

Multiple callbacks need to close the same modal (save, delete, cancel). Without `allow_duplicate`, Dash throws an error about multiple callbacks targeting the same output.

**prevent_initial_call:**

```python
# api/dash/callbacks.py:61

@callback(..., prevent_initial_call=True)
```

Skip the callback on page load. Useful for action handlers that should only fire on user interaction.

---

## State Management

State in Dash is layered:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LAYER 1: Browser localStorage                             │
│                                                                             │
│   session-id-store  ─────────────────  UUID, persists across sessions       │
│                                                                             │
│   Survives: tab close, browser restart, system reboot                       │
│   Lost: clearing browser data, different browser/device                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ syncs via dcc.Store
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LAYER 2: dcc.Store (in-memory)                            │
│                                                                             │
│   shortlist-store   ─────────────────  List of dish UIDs                    │
│   dish-modal-mode   ─────────────────  "add" or "edit"                      │
│   dish-modal-uid    ─────────────────  UID being edited                     │
│                                                                             │
│   Survives: nothing (reset on page refresh)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ callbacks read/write
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LAYER 3: Backend AppContext                               │
│                                                                             │
│   catalogue.list_dishes()  ──────────  All dishes for this user             │
│   planning.get_shortlist() ──────────  Persisted shortlist                  │
│   planning.list_plans()    ──────────  Generated meal plans                 │
│                                                                             │
│   Survives: across requests (in-memory cache)                               │
│   Lost: server restart, deploy                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Not Redux-Style?

In React, you might use Redux or Zustand for global state management. Dash doesn't need this because:

1. **Callbacks ARE state management.** When you define `Output("store", "data")`, you're defining how state changes.
2. **State lives in components.** `dcc.Store` holds the data; callbacks transform it.
3. **No client-side logic.** Redux exists because React needs client-side state coordination. Dash's state lives on the server.

The Dash pattern: State flows from Stores → through callbacks → back to Stores (and components).

### State Flow Example: Adding a Dish

```
User clicks "→" on dish card (id={"type": "add-dish", "uid": "DISH-123"})
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  update_shortlist_store() callback fires                                   │
│  - Input: {"type": "add-dish", "uid": ALL}                                 │
│  - ctx.triggered_id = {"type": "add-dish", "uid": "DISH-123"}              │
│  - Returns: current_shortlist + ["DISH-123"]                               │
└───────────────────────────────────────────────────────────────────────────┘
        │
        │ Output: shortlist-store.data = ["DISH-123"]
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  render_columns() callback fires (Input: shortlist-store.data)             │
│  - Gets session_id from session-id-store                                   │
│  - Gets app_ctx = _get_context(session_id)                                 │
│  - Filters dishes: catalogue vs shortlist                                  │
│  - Returns: new catalogue-cards, shortlist-cards                           │
└───────────────────────────────────────────────────────────────────────────┘
        │
        │ UI updates: dish moves from left column to right column
        ▼
    User sees dish in shortlist
```

---

## Styling Approach

### Theme Tokens (`theme.py`)

All presentation values live in one file:

```python
# theme.py:16-55

CUISINE_FLAG: dict[Cuisine, str] = {
    Cuisine.KOREAN: "🇰🇷",
    Cuisine.JAPANESE: "🇯🇵",
    Cuisine.CHINESE: "🇨🇳",
    # ...
}

CATEGORY_COLOR: dict[Category, CategoryColor] = {
    Category.GREENS: CategoryColor(muted="#E8F5E9", bold="#3D6B4A"),
    Category.LEGUMES: CategoryColor(muted="#F5EFEA", bold="#7D6554"),
    # ...
}
```

**Why a Python file, not CSS variables alone?**

1. **Type safety.** If I misspell `Category.GREENS`, Python catches it. If I misspell `--cat-greens-bg`, CSS silently fails.
2. **Single source of truth.** Components use `CUISINE_FLAG[dish.cuisine]`. CSS uses generated variables. Both from one place.
3. **Computed values.** I can derive CSS from the Python dict:

```python
# theme.py:63-70

def generate_category_css_vars() -> str:
    """Generate CSS variables for category colors."""
    lines = [":root {"]
    for cat, color in CATEGORY_COLOR.items():
        slug = cat.value.replace("_", "-")
        lines.append(f"  --cat-{slug}-bg: {color.muted};")
        lines.append(f"  --cat-{slug}-text: {color.bold};")
    lines.append("}")
    return "\n".join(lines)
```

This CSS is injected into the HTML head at runtime.

### CSS Design System (`assets/style.css`)

I organized the CSS into systems:

**Variables (lines 5-59):**
```css
:root {
    /* Brand */
    --color-brand: #F4A940;
    --color-brand-hover: #E09930;

    /* Typography */
    --font-display: "BBH Hegarty", sans-serif;
    --font-card: "Nunito", sans-serif;

    /* Spacing */
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 12px;
}
```

**Chiclets (lines 133-190):** Pill-shaped elements with variants:
- `.chiclet--section` - Column headers
- `.chiclet--action` - Primary CTA
- `.chiclet--link` - Text links
- `.chiclet--counter` - Count badges

**Cards (lines 197-267):** Dish cards with hover states:
- `.card` - Base with border highlight on hover
- `.card__header` - Title + flag + actions row
- `.card__actions` - Hidden until hover

**Tags (lines 272-305):** Category pills using CSS variables from `theme.py`.

### Typography Hierarchy

| Element | Font | Size | Usage |
|---------|------|------|-------|
| Hero headlines | BBH Hegarty | 52px | Score display |
| Section headers | DM Sans | 16px | Column titles |
| Card titles | Nunito | 16px | Dish names |
| Body text | Inter | 14px | Descriptions |
| Tags | Nunito | 12px | Category pills |

**Why four fonts?**

Each serves a purpose:
- **BBH Hegarty**: Display font with personality. Used sparingly for impact.
- **DM Sans**: Clean, modern. Good for UI chrome.
- **Nunito**: Rounded, friendly. Warms up the card content.
- **Inter**: Workhorse readable font. Body text, long content.

Too many fonts? Maybe. But they're all Google Fonts, loaded in one request. The visual hierarchy is worth it.

---

## The "No JavaScript" Philosophy

### What It Means

I committed to keeping all logic in Python:

1. **No custom JavaScript files.** Everything in `assets/` is CSS.
2. **No clientside_callback.** Dash allows client-side callbacks in JavaScript. I avoided them.
3. **Accept Dash's constraints.** If Dash can't do it server-side, I redesigned or skipped the feature.

### When I Broke It

I didn't write any JavaScript. But I rely on Dash's built-in clientside behavior:
- `dcc.Store` with `storage_type="local"` uses JavaScript localStorage
- Mantine components have JavaScript interactions (dropdowns, modals)

This is "JavaScript I didn't write." I'm okay with that.

### The Benefits

**One language to debug.** When the app misbehaves, I open the Python debugger. No context-switching to browser devtools.

**No build toolchain.** No webpack, no babel, no node_modules. Just `uv run` and go.

**Simpler deployment.** One Docker image, one process, one thing to monitor.

**The cost:** Some interactions feel sluggish. Every click is a server round-trip. For a meal planner, this is acceptable. For a real-time collaboration tool, it wouldn't be.

---

## Mistakes I Made

### The Monolithic `generate_plan()` Callback

This callback is 270 lines long:

```python
# api/dash/callbacks.py:151-424

@callback(
    Output("results-modal", "opened"),
    Output("results-hero-score", "children"),
    Output("results-hero-feedback", "children"),
    # ... 12 more outputs
)
def generate_plan(n_clicks, shortlist_uids, session_id):
    """Generate plan and diversity analysis from shortlisted dishes."""
    # Line 160: Guard clause
    # Line 170: Get context and dishes
    # Line 180: Call planning service
    # Line 200: Calculate metrics
    # Line 250: Generate UI sections
    # Line 300: Build hero score
    # Line 350: Build color bars
    # Line 400: Build week cards
    # Return 15 values
```

**The problem:** This callback does too much:
1. Fetches data from services
2. Calculates metrics
3. Generates copy via `report_copy` module
4. Builds 5+ UI sections
5. Handles errors

If any part breaks, the whole callback fails. Testing is painful - you need to mock everything to test anything.

**How I'd fix it:** Break into smaller callbacks with intermediate stores:

```python
# Better approach:
# 1. generate_plan() -> Output("plan-data-store", "data")
# 2. render_hero() -> Input("plan-data-store", "data")
# 3. render_colors() -> Input("plan-data-store", "data")
# 4. render_weeks() -> Input("plan-data-store", "data")
```

Each callback has one job. Easier to test, debug, and maintain.

### Module-Level Dish Cache

Already discussed above. Don't cache unless profiling proves you need it.

### No Validation Feedback

```python
# api/dash/callbacks.py:518-520

if not name or not cuisine:
    return True, shortlist  # Modal stays open, but no error message!
```

**The problem:** When validation fails, the modal stays open, but the user doesn't know why. They just see... nothing happening.

**How I'd fix it:** Add a validation message output:

```python
Output("dish-modal-error", "children"),

if not name:
    return True, shortlist, "Name is required"
if not cuisine:
    return True, shortlist, "Cuisine is required"
```

### Mixed Concerns in `save_dish()`

```python
# api/dash/callbacks.py:516-553

def save_dish(n_clicks, mode, uid, name, cuisine, categories, tags, recipe, shortlist, session_id):
    """Save dish (add new or update existing)."""
    # Validation
    # Create dish model
    # Call catalogue service
    # Update shortlist if new dish
    # Return: close modal, updated shortlist
```

**The problem:** This callback does UI coordination (close modal) AND business logic (save dish) AND state management (update shortlist). Classic "God callback."

**How I'd fix it:** Separate concerns into multiple callbacks, or at least extract the business logic into a service method.

---

## What I'd Do Differently

### Intermediate Stores for Complex State

Instead of one giant callback producing 15 outputs, use intermediate stores:

```python
# Step 1: Generate plan data
@callback(
    Output("analysis-store", "data"),
    Input("generate-btn", "n_clicks"),
    State("shortlist-store", "data"),
    State("session-id-store", "data"),
)
def generate_analysis(n_clicks, shortlist, session_id):
    # Calculate all metrics
    return {"scores": {...}, "weeks": [...], "feedback": {...}}

# Step 2: Render from store (can be multiple callbacks)
@callback(
    Output("results-hero-score", "children"),
    Input("analysis-store", "data"),
)
def render_hero(data):
    return data["scores"]["overall"]
```

Benefits:
- Each callback is small and testable
- Callbacks can run in parallel
- Failure in one renderer doesn't break others

### Clear Cache on Mutations

```python
# In save_dish():
global _cached_dishes
_cached_dishes = None  # Invalidate cache

# In delete_dish():
global _cached_dishes
_cached_dishes = None  # Invalidate cache
```

Or better: don't cache at all. Measure first.

### Toast Notifications

User feedback is important. "Dish saved!" "Plan generated!" "Error: name required."

Mantine has `dmc.Notification`. I should use it:

```python
Output("notification-container", "children"),

# On success:
return dmc.Notification(
    title="Success",
    message="Dish saved!",
    color="green",
)
```

### Loading States

The "Generate Plan" button should show a spinner during processing:

```python
@callback(
    Output("generate-btn", "loading"),
    Input("generate-btn", "n_clicks"),
)
def show_loading(n_clicks):
    return True  # Mantine button shows spinner

# Then reset in generate_plan callback
```

---

## Longlist of Things to Do

### Code Cleanup

- [ ] **Split `generate_plan()` into smaller callbacks** - Use intermediate stores
- [ ] **Add validation feedback to modals** - Show error messages, not silent failure
- [ ] **Invalidate module cache on dish changes** - Or remove the cache entirely
- [ ] **Extract UI generation from `generate_plan()`** - Callbacks should coordinate, not render

### UX Enhancements

- [ ] **Loading states during plan generation** - Spinner on button
- [ ] **Toast notifications for actions** - "Dish saved!", "Deleted!"
- [ ] **Keyboard shortcuts** - Enter to save modal, Escape to close
- [ ] **Optimistic updates** - Show change immediately, sync in background
- [ ] **Undo support** - "Dish deleted. Undo?"

### Architecture

- [ ] **Consider clientside callbacks for instant feedback** - For things like "show loading spinner"
- [ ] **Add error boundaries** - Graceful degradation when callbacks fail
- [ ] **Implement proper loading states** - Skeleton screens, not empty content
- [ ] **Add E2E tests** - Playwright or similar for callback integration testing

### Performance

- [ ] **Profile callback execution times** - Find the slow ones
- [ ] **Consider response caching** - For expensive computations
- [ ] **Lazy load modal content** - Don't render until opened

---

## See Also

- [App Architecture](app-architecture.md) - Domain models and services
- [Session Architecture](session-architecture.md) - Multi-user support
- [Dash README](../api/dash/README.md) - Quick reference for the Dash layer
