# Palate - Dash Web UI

> A kanban-style meal planning interface built with Dash and Mantine components.

## Architecture

```
api/dash/
├── app.py              # Dash app entry point, layout, theme
├── callbacks.py        # All reactive callbacks (add/remove, filters, charts)
├── components.py       # Reusable Mantine component factories
└── assets/
    └── style.css       # Design system (CSS variables, chiclets, cards, tags)
```

### Layer Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         app.py                                   │
│  - Dash app initialization                                       │
│  - MantineProvider theme (saffron palette)                       │
│  - AppShell layout (header + main)                               │
│  - Injects CSS variables from theme.py                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  components.py  │  │  callbacks.py   │  │   style.css     │
│  ───────────────│  │  ───────────────│  │  ───────────────│
│  dish_card()    │  │  Shortlist      │  │  CSS variables  │
│  dish_column()  │  │  management     │  │  from theme.py  │
│  dish_modal()   │  │                 │  │                 │
│  results_modal()│  │  Filter/search  │  │  .chiclet--*    │
│  info_modal()   │  │  callbacks      │  │  .card, .card__*│
│  category_tag() │  │                 │  │  .tag--category │
│  cuisine_flag() │  │  Chart gen      │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                   │
         │                   │
         ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                        theme.py                                  │
│  Single source of truth for presentation tokens                  │
│  - CUISINE_FLAG: emoji flags for cuisines                        │
│  - CATEGORY_COLOR: muted/bold color pairs                        │
│  - generate_category_css_vars(): CSS variable injection          │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     core/ (domain layer)                         │
│  - Category, Cuisine enums                                       │
│  - Dish models                                                   │
│  - Planning services                                             │
└─────────────────────────────────────────────────────────────────┘
```

## Design System

### Theme Tokens (`theme.py`)

All presentation values live in `meal_planning/theme.py`:

```python
# Cuisine flags (emoji)
CUISINE_FLAG: dict[Cuisine, str] = {
    Cuisine.KOREAN: "🇰🇷",
    Cuisine.JAPANESE: "🇯🇵",
    ...
}

# Category colors (muted bg + bold text)
CATEGORY_COLOR: dict[Category, CategoryColor] = {
    Category.GREENS: CategoryColor("#E8F5E9", "#3D6B4A"),
    ...
}
```

CSS variables are auto-generated and injected into the HTML head:
```css
:root {
  --cat-greens-bg: #E8F5E9;
  --cat-greens-text: #3D6B4A;
  ...
}
```

### CSS Classes (`style.css`)

**Chiclets** - Pill-shaped buttons/labels:
- `.chiclet--section` - Column headers ("YOUR PALETTE")
- `.chiclet--action` - Primary CTA ("See Your Colors")
- `.chiclet--link` - Navigation links ("Why Palate?")
- `.chiclet--counter` - Counts ("12 dishes")

**Cards** - Dish cards with hover states:
- `.card` - Base card with border highlight on hover
- `.card__header` - Title + flag + actions row
- `.card__title` - Nunito font, warm typography
- `.card__flag` - Cuisine emoji
- `.card__actions` - Hidden until hover
- `.card__tags` - Category tag container

**Tags** - Category pills:
- `.tag--category[data-category="greens"]` - Uses CSS variables

### Typography

| Font | Usage |
|------|-------|
| BBH Hegarty | Display headers, section labels |
| DM Sans | Secondary headers |
| Nunito | Card titles, tags (warm feel) |
| Inter | Body text |

## Running

### Development (hot reload)

```bash
./devops/scripts/dev.sh
# Opens http://localhost:8051
```

### Docker (production)

```bash
docker build -f devops/docker/Dockerfile.dash-app -t palate-dash-app .
docker run -d -p 8050:8060 --name palate-app palate-dash-app
# Opens http://localhost:8050
```

## Data Flow

### Adding a Dish to Shortlist

```
User clicks "→" on dish card
        │
        ▼
Pattern-matching callback triggers
({"type": "add-dish", "uid": "..."})
        │
        ▼
update_shortlist_store() adds UID to dcc.Store
        │
        ▼
render_columns() re-renders both columns
(dish moves from Catalogue to Shortlist)
```

### Generating Results

```
User clicks "See Your Colors"
        │
        ▼
generate_plan() callback
        │
        ├── Fetches dishes from catalogue
        ├── Calls planning.create_plan()
        ├── Builds week cards
        ├── Generates Plotly charts with CATEGORY_COLOR
        └── Opens results modal
```

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | App init, layout, theme, CSS injection |
| `callbacks.py` | All reactive logic |
| `components.py` | Component factories (dish_card, modals, etc.) |
| `assets/style.css` | Full design system |
| `../../theme.py` | Color/flag tokens (single source of truth) |
