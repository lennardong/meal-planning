# Palate — Dash App Design Specs

## Brand Overview

**App Name:** Palate  
**Tagline:** Expand Your Palette  
**Core Message:** Count colors, cuisines, and kingdoms—not calories.

---

## Color System

### Primary Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Saffron** | `#F4A940` | 244, 169, 64 | Primary accent, buttons, highlights |
| **Aubergine** | `#5B3E6B` | 91, 62, 107 | Secondary accent, headers, emphasis |
| **Canvas** | `#FAF9F7` | 250, 249, 247 | Page background |
| **Charcoal** | `#2D2D2D` | 45, 45, 45 | Body text |

### Food Category Tag Colors

Use these for cuisine and category tags on dish cards:

| Category | Hex | Tag Background | Tag Text |
|----------|-----|----------------|----------|
| **Greens** | `#4A7C59` | `#E8F5E9` | `#4A7C59` |
| **Legumes** | `#8B5A2B` | `#EFEBE9` | `#8B5A2B` |
| **Grains** | `#E8C547` | `#FFFDE7` | `#A68F00` |
| **Fermented** | `#5BA4A4` | `#E0F7FA` | `#5BA4A4` |
| **Alliums** | `#7B4B94` | `#F3E5F5` | `#7B4B94` |
| **Protein** | `#4A6FA5` | `#E3F2FD` | `#4A6FA5` |
| **Fruits** | `#D46A84` | `#FCE4EC` | `#D46A84` |
| **Nuts/Seeds** | `#D4883E` | `#FFF3E0` | `#D4883E` |
| **Dairy** | `#9E9E9E` | `#F5F5F5` | `#757575` |
| **Red/Orange Veg** | `#C1513D` | `#FFEBEE` | `#C1513D` |

### Cuisine Tag Colors

| Cuisine | Hex | Tag Background | Tag Text |
|---------|-----|----------------|----------|
| **Chinese** | `#E53935` | `#FFEBEE` | `#C62828` |
| **Japanese** | `#FB8C00` | `#FFF3E0` | `#E65100` |
| **Indian** | `#F4A940` | `#FFFDE7` | `#F57F17` |
| **Italian** | `#43A047` | `#E8F5E9` | `#2E7D32` |
| **Mexican** | `#00897B` | `#E0F2F1` | `#00695C` |
| **Thai** | `#8E24AA` | `#F3E5F5` | `#6A1B9A` |
| **Western** | `#5C6BC0` | `#E8EAF6` | `#3949AB` |
| **Korean** | `#D81B60` | `#FCE4EC` | `#AD1457` |
| **Mediterranean** | `#039BE5` | `#E1F5FE` | `#0277BD` |

---

## Typography

### Font Stack (Google Fonts)

**Primary (Headlines):**
```css
font-family: 'DM Sans', sans-serif;
font-weight: 700;
```

**Secondary (Body):**
```css
font-family: 'Inter', sans-serif;
font-weight: 400;
```

**Monospace (Scores/Data):**
```css
font-family: 'Space Grotesk', sans-serif;
font-weight: 500;
```

### Type Scale

| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| App Title | DM Sans | 32px | 700 | Aubergine `#5B3E6B` |
| Tagline | Inter | 16px | 400 italic | Charcoal `#6B6B6B` |
| Section Headers | DM Sans | 20px | 700 | Charcoal `#2D2D2D` |
| Body Text | Inter | 15px | 400 | Charcoal `#2D2D2D` |
| Card Title | DM Sans | 14px | 600 | Charcoal `#2D2D2D` |
| Tags | Inter | 11px | 500 | Varies by category |
| Scores/Numbers | Space Grotesk | 24px | 500 | Saffron `#F4A940` |

---

## Component Styling

### Page Container

```css
background-color: #FAF9F7;
padding: 40px 60px;
max-width: 1400px;
margin: 0 auto;
```

### Section Cards (Intro, How It Works, etc.)

```css
background-color: #FFFFFF;
border-radius: 12px;
padding: 32px;
box-shadow: 0 1px 3px rgba(0,0,0,0.08);
margin-bottom: 24px;
```

### Dish Cards

```css
background-color: #FFFFFF;
border: 1px solid #E8E8E8;
border-radius: 8px;
padding: 16px;
transition: box-shadow 0.2s ease;

/* Hover state */
&:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-color: #F4A940;
}
```

### Tags (Cuisine & Category)

```css
display: inline-block;
padding: 4px 10px;
border-radius: 4px;
font-size: 11px;
font-weight: 500;
text-transform: uppercase;
letter-spacing: 0.5px;
margin-right: 6px;
margin-bottom: 6px;
```

### Primary Button (Generate Plan)

```css
background-color: #F4A940;
color: #FFFFFF;
font-family: 'DM Sans', sans-serif;
font-weight: 600;
font-size: 14px;
padding: 12px 24px;
border-radius: 8px;
border: none;
cursor: pointer;
transition: background-color 0.2s ease;

&:hover {
  background-color: #E09830;
}
```

### Secondary Button

```css
background-color: transparent;
color: #5B3E6B;
border: 2px solid #5B3E6B;
font-family: 'DM Sans', sans-serif;
font-weight: 600;
font-size: 14px;
padding: 10px 22px;
border-radius: 8px;

&:hover {
  background-color: #5B3E6B;
  color: #FFFFFF;
}
```

### Input Fields / Search

```css
background-color: #FFFFFF;
border: 1px solid #E0E0E0;
border-radius: 8px;
padding: 12px 16px;
font-family: 'Inter', sans-serif;
font-size: 14px;

&:focus {
  border-color: #F4A940;
  outline: none;
  box-shadow: 0 0 0 3px rgba(244, 169, 64, 0.15);
}
```

---

## Renamed UI Elements

Update these labels throughout the app:

| Old Name | New Name |
|----------|----------|
| Rewilding the Gut | **Palate** |
| A Monthly Meal Planner | **Expand Your Palette** |
| Why This Planner? | **Why Palate?** |
| Catalogue | **Your Palette** |
| Shortlist | **This Week** |
| Generate Plan | **See Your Colors** |
| diversity score | **Palate Score** |
| cooking categories | **cooking categories** *(keep)* |
| Build your catalogue | **Build Your Palette** |
| Create a shortlist | **Pick Your Week** |
| Generate a plan | **See Your Colors** |

---

## Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  PALATE                           [Expand Your Palette] │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Why Palate?                                      │  │
│  │  [Intro content from app_intro.md]                │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────┐    ┌──────────────────────┐   │
│  │  CATALOGUE │    │  CANVAS           │   │
│  │  ────────────────   │    │  ────────────────    │   │
│  │  [Search]     [All] │    │  [Search]     [All]  │   │
│  │                     │    │                      │   │
│  │  ┌─────┐ ┌─────┐   │    │                      │   │
│  │  │Dish │ │Dish │   │    │  [Empty state or     │   │
│  │  │Card │ │Card │   │    │   selected dishes]   │   │
│  │  └─────┘ └─────┘   │    │                      │   │
│  │  ┌─────┐ ┌─────┐   │    │                      │   │
│  │  │Dish │ │Dish │   │    │                      │   │
│  │  │Card │ │Card │   │    │                      │   │
│  │  └─────┘ └─────┘   │    │                      │   │
│  └─────────────────────┘    └──────────────────────┘   │
│                                                         │
│            [ See Your Colors ]  (Primary Button)        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Dash-Specific Notes

### Installing Fonts

Add to your `assets/` folder or include in the app layout:

```python
app = Dash(__name__)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600&family=Space+Grotesk:wght@400;500;600&display=swap" rel="stylesheet">
        {%metas%}
        <title>Palate</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''
```

### CSS Variables (for assets/style.css)

```css
:root {
  /* Brand Colors */
  --color-saffron: #F4A940;
  --color-saffron-hover: #E09830;
  --color-aubergine: #5B3E6B;
  --color-canvas: #FAF9F7;
  --color-charcoal: #2D2D2D;
  --color-charcoal-light: #6B6B6B;
  
  /* UI Colors */
  --color-border: #E0E0E0;
  --color-card-bg: #FFFFFF;
  --color-shadow: rgba(0,0,0,0.08);
  
  /* Typography */
  --font-display: 'DM Sans', sans-serif;
  --font-body: 'Inter', sans-serif;
  --font-mono: 'Space Grotesk', sans-serif;
  
  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-xxl: 48px;
  
  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
}
```

### Tag Component Example (Python)

```python
def create_tag(label, category_type):
    """
    category_type: 'cuisine' or one of the food categories
    """
    colors = {
        'CHINESE': {'bg': '#FFEBEE', 'text': '#C62828'},
        'JAPANESE': {'bg': '#FFF3E0', 'text': '#E65100'},
        'GREENS': {'bg': '#E8F5E9', 'text': '#4A7C59'},
        'LEGUMES': {'bg': '#EFEBE9', 'text': '#8B5A2B'},
        'FERMENTED': {'bg': '#E0F7FA', 'text': '#5BA4A4'},
        'ALLIUMS': {'bg': '#F3E5F5', 'text': '#7B4B94'},
        'GRAINS': {'bg': '#FFFDE7', 'text': '#A68F00'},
        # ... add others
    }
    
    color = colors.get(label.upper(), {'bg': '#F5F5F5', 'text': '#757575'})
    
    return html.Span(
        label,
        style={
            'backgroundColor': color['bg'],
            'color': color['text'],
            'padding': '4px 10px',
            'borderRadius': '4px',
            'fontSize': '11px',
            'fontWeight': '500',
            'textTransform': 'uppercase',
            'letterSpacing': '0.5px',
            'marginRight': '6px',
            'display': 'inline-block'
        }
    )
```

---

## Empty States

### This Week (Shortlist) — Empty

> **Nothing here yet**  
> Add dishes from Your Palette to start building your week.

### Your Palette — Empty

> **Your palette is blank**  
> Hit the + button to add your first dish.

### After Generating Plan

> **Your Palate Score: 73%**  
> You're hitting 8 of 10 colors this week. Nice range.

---

## Quick Reference: Voice Reminders

When writing any UI copy, remember:

- **Direct.** "Add dishes" not "You can add dishes here"
- **Warm.** "Nice range" not "Optimal diversity achieved"
- **Specific.** "8 of 10 colors" not "Good variety"
- **No jargon.** "Fermented foods" not "Probiotic-rich options"

---

*Questions? Refer to the full grand-guidelines.md for voice guidelines and extended examples.*