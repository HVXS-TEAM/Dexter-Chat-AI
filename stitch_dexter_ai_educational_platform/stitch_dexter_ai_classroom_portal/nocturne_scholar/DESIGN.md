---
name: Nocturne Scholar
colors:
  surface: '#051424'
  surface-dim: '#051424'
  surface-bright: '#2c3a4c'
  surface-container-lowest: '#010f1f'
  surface-container-low: '#0d1c2d'
  surface-container: '#122131'
  surface-container-high: '#1c2b3c'
  surface-container-highest: '#273647'
  on-surface: '#d4e4fa'
  on-surface-variant: '#c8c4d7'
  inverse-surface: '#d4e4fa'
  inverse-on-surface: '#233143'
  outline: '#928ea0'
  outline-variant: '#474555'
  surface-tint: '#c7bfff'
  primary: '#c7bfff'
  on-primary: '#29009f'
  primary-container: '#8d7fff'
  on-primary-container: '#23008d'
  inverse-primary: '#5843dc'
  secondary: '#85d0f6'
  on-secondary: '#003547'
  secondary-container: '#00698a'
  on-secondary-container: '#b1e3ff'
  tertiary: '#3bddc7'
  on-tertiary: '#003731'
  tertiary-container: '#00a392'
  on-tertiary-container: '#00302a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e4dfff'
  primary-fixed-dim: '#c7bfff'
  on-primary-fixed: '#170065'
  on-primary-fixed-variant: '#4023c4'
  secondary-fixed: '#c0e8ff'
  secondary-fixed-dim: '#85d0f6'
  on-secondary-fixed: '#001e2b'
  on-secondary-fixed-variant: '#004d66'
  tertiary-fixed: '#61fae3'
  tertiary-fixed-dim: '#3bddc7'
  on-tertiary-fixed: '#00201c'
  on-tertiary-fixed-variant: '#005047'
  background: '#051424'
  on-background: '#d4e4fa'
  surface-variant: '#273647'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.03em
  headline-xl:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0.005em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-sm: 1rem
  gutter-lg: 2rem
  margin: 2rem
  margin-sm: 1rem
  margin-lg: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 2rem
---

## Brand & Style
The design system embodies a refined, focused, and intellectually stimulating environment tailored for high-performance academic and cognitive pursuits. Aimed at university students, researchers, and lifelong learners, the interface evokes sustained focus, quiet intellect, and progressive discovery. 

The aesthetic synthesizes modern French educational SaaS elegance with deep-space glassmorphism. It rejects visual clutter in favor of crisp spatial organization, luminous micro-accents, and subtle physical layering. Glass-like translucent planes anchor complex study workflows—such as synthetic note generation, concept mapping, and active recall queries—without overwhelming visual bandwidth. The emotional tone is authoritative yet frictionless: a personal, distraction-free digital atelier designed for deep work.

## Colors
The palette leverages high-contrast luminescence over an abyss of deep navy tones, minimizing eye fatigue during prolonged study sessions while preserving sharp legibility.

- **Background Canvas (`#020b17`):** The foundational substrate representing quiet depth.
- **Surface Layer 1 (`#0b1729`):** Primary structural surface for sidebars, persistent panels, and resting card containers.
- **Surface Layer 2 (`#1d2a3d`):** Elevated surface for active modules, interactive cards, modals, and dropdown overlays.
- **Primary Accent (`#7a68ff`):** Energetic violet-purple, utilized for primary calls to action, active study states, AI response highlights, and key focus milestones.
- **Secondary Accent (`#8ed9ff`):** Crisp ice-blue, employed for citations, cognitive hints, contextual badges, and secondary analytical data points.
- **Text & Contrast Structure:**
  - **High-Contrast Text (`#ffffff`):** Dedicated to primary headers, actionable typography, and focused prompts.
  - **Muted Contrast Text (`#94a3b8` / Light Slate Gray):** Secondary metadata, inactive states, timestamps, and descriptive explanatory body copy.
  - **Subtle Surface Border (`rgba(142, 217, 255, 0.1)` to `rgba(255, 255, 255, 0.08)`): Crisp 1px division demarcating modular containers.

## Typography
Constructed uniformly with Inter, typography maintains Swiss-level discipline across dense educational layouts. Tight negative tracking in large display weights ensures headlines feel sharp, structured, and editorial. In contrast, body copy leverages generous line-heights (1.55x to 1.6x) and balanced neutral tracking to preserve visual clarity when reading long-form generated study guides or synthesized texts. Labels and metadata employ heightened medium/semibold weights with positive tracking to guarantee scanability against deep navy backdrops.

## Layout & Spacing
Optimized specifically for fixed-canvas workstation viewports (target canvas: 1440x1024), the layout implements a structured multi-pane app shell:
- **Left Command Rail:** 280px persistent navigation and subject directory.
- **Primary Center Stage:** Flexible 12-column workspace for notes, AI conversation, and source documents.
- **Contextual Inspector / Flashcard Panel:** 380px collapsible panel for contextual study tools.

The spacing rhythm is governed by an 8pt architectural matrix (subdivided to 4pt micro-steps). Gutters maintain a consistent `1.5rem` (24px) breathability across multi-column panes. Container interiors employ `space-lg` (20px) for regular cards, expanding to `space-xl` (32px) for elevated hero canvases, ensuring content density remains high without feeling compressed.

## Elevation & Depth
Visual hierarchy is articulated through frosted glassmorphism coupled with subtle ambient occlusion rather than harsh Drop shadows.

- **Base Floor (`#020b17`):** Unadorned foundational canvas.
- **Tier 1 Surfaces (`rgba(11, 23, 41, 0.85)` + `backdrop-filter: blur(16px)`):** Panels, navigation rails, and default card backgrounds. Outlined with a fine, continuous 1px stroke of `rgba(255, 255, 255, 0.06)`.
- **Tier 2 Surfaces (`rgba(29, 42, 61, 0.8)` + `backdrop-filter: blur(24px)`):** Hovered cards, floating study controls, command palettes, and active tool drawers. Framed by a subtle top-lit inner highlight (`linear-gradient(180deg, rgba(142, 217, 255, 0.15) 0%, rgba(255, 255, 255, 0.03) 100%)`) and an ambient shadow: `0 12px 32px -4px rgba(2, 11, 23, 0.6)`.
- **Primary Accent Glow:** Interactive elements carrying focus or processing states cast an ambient primary drop-glow: `0 0 24px -4px rgba(122, 104, 255, 0.3)`.

## Shapes
Geometry is strictly segmented to provide tactile feedback and structural clarity:
- **Cards & Structural Containers:** Standardized to a signature `18px` border radius, delivering a soft, modern container identity that eases ocular transitions between juxtaposed panes.
- **Controls & Form Elements:** Buttons, text input boxes, segmented pills, and dropdown selectors use a strict `12px` border radius for ergonomics.
- **Micro-Indicators & Status Chips:** Pill-shaped (`9999px`) or `6px` radius depending on inline context.

## Components

### Buttons
- **Primary:** Background of `#7a68ff` with crisp `#ffffff` text, 12px border radius, 12px vertical and 20px horizontal padding. On hover, background shifts to `#8c7dff` accompanied by a soft violet glow (`0 0 20px rgba(122, 104, 255, 0.4)`).
- **Secondary:** Background of `rgba(29, 42, 61, 0.6)`, 1px border of `rgba(142, 217, 255, 0.2)`, text in `#8ed9ff`. On hover, border shifts to `#8ed9ff` with surface illumination.
- **Ghost / Icon:** Transparent fill, `#94a3b8` icon fill, shifting to `#ffffff` with a subtle surface background of `rgba(255, 255, 255, 0.05)` on hover. Icons are sized strictly at 24px (Material Symbols).

### Input Fields
- Constructed with a 12px radius, a background of `#0b1729`, and a 1px border of `rgba(255, 255, 255, 0.1)`. Placeholder text sits in `#94a3b8`.
- Focus state: Border transitions to `#7a68ff`, accompanied by a diffuse outline glow: `0 0 0 3px rgba(122, 104, 255, 0.2)`.

### Cards
- Set to an 18px radius with a layered surface fill (`#0b1729` base or `rgba(11, 23, 41, 0.7)` with `backdrop-filter: blur(16px)`).
- Enclosed with a 1px perimeter border in `rgba(255, 255, 255, 0.07)`.
- Interactive cards elevate on hover using `#1d2a3d`, a border tint of `rgba(142, 217, 255, 0.25)`, and a 2px upward Y-axis translation.

### Chips & Badges
- Educational metadata tags (e.g., subject tags, difficulty indicators) feature a pill radius (`9999px`), 4px vertical / 10px horizontal padding, and a typography standard of `label-sm`.
- Ice blue chip: Background `rgba(142, 217, 255, 0.1)`, text `#8ed9ff`, border `1px solid rgba(142, 217, 255, 0.2)`.
- Violet chip: Background `rgba(122, 104, 255, 0.12)`, text `#7a68ff`, border `1px solid rgba(122, 104, 255, 0.25)`.

### Checkboxes & Radio Buttons
- Formed with 12px container logic (checkboxes: 4px radius, radios: full circle). Sized to 20x20px.
- Unchecked: 1.5px border of `#94a3b8`, transparent interior.
- Checked: `#7a68ff` background with white checkmark icon or center dot, accompanied by an ambient violet focus indicator.

### Lists & Flashcard Feed
- List items feature alternating subtle highlight separators (`rgba(255, 255, 255, 0.04)`), with active items taking on a left-accent border (3px solid `#7a68ff`) and a background gradient bleeding from `rgba(122, 104, 255, 0.08)` to transparent.