---
name: Aether Intelligence Light
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#464555'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#712ae2'
  on-secondary: '#ffffff'
  secondary-container: '#8a4cfc'
  on-secondary-container: '#fffbff'
  tertiary: '#7e3000'
  on-tertiary: '#ffffff'
  tertiary-container: '#a44100'
  on-tertiary-container: '#ffd2be'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#eaddff'
  secondary-fixed-dim: '#d2bbff'
  on-secondary-fixed: '#25005a'
  on-secondary-fixed-variant: '#5a00c6'
  tertiary-fixed: '#ffdbcc'
  tertiary-fixed-dim: '#ffb695'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7b2f00'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
  surface-base: '#FFFFFF'
  surface-tinted: '#F8F7FF'
  surface-subtle: '#F1F0FB'
  gradient-start: '#3B82F6'
  gradient-end: '#8B5CF6'
  domain-green: '#10B981'
  domain-orange: '#F59E0B'
  domain-blue: '#0EA5E9'
  text-primary: '#0F172A'
  text-secondary: '#475569'
  text-tertiary: '#94A3B8'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 40px
  xl: 64px
  gutter: 24px
  margin: 32px
  max_width: 1440px
---

## Brand & Style

This design system reimagines a high-intelligence AI environment for a high-clarity light mode. It evolves from "Midnight Minimalism" to **Luminous Sophistication**, targeting students and researchers who require a clean, airy, and focused workspace.

The aesthetic direction is **Pristine Glassmorphism** layered over a **Soft-SaaS** foundation. It replaces deep shadows with subtle tonal shifts and translucent overlays to maintain a sense of lightness and technical precision.

Key attributes:
- **Luminous Depth:** Utilizing bright whites and faint lavender-tinted grays to create an expansive, non-fatiguing environment.
- **Spectrum Accents:** The primary blue-to-purple gradient is preserved for high-impact visual cues, acting as the "pulse" of the AI within a clean container.
- **Academic Clarity:** High-contrast typography and a rigid adherence to the 8px grid ensure that complex data remains the focal point.
- **Approachable Tech:** The signature large border radii (18-20px) are maintained to ensure the interface feels organic and inviting rather than sterile.

## Colors

The light mode palette transitions away from deep blacks to a foundation of "Bright Air."

- **Foundations:** The primary background is pure White (#FFFFFF). Secondary surfaces use a very light purple-tinted grey (#F8F7FF) to provide structural separation without adding visual weight.
- **Accents:** The interaction model relies on the signature **Aether Gradient** (Blue #3B82F6 to Violet #8B5CF6). Use this for primary buttons, progress indicators, and active states.
- **Domain Indicators:** Maintain specific hues (Green, Orange, Blue) for subject categorization. In light mode, these should be used as solid accents or high-saturation icons against the light backgrounds.
- **Neutrals:** Text is rendered in a deep Navy-Black (#0F172A) for maximum legibility. Secondary labels use a Slate Grey (#475569) to establish a clear information hierarchy.

## Typography

This design system uses **Inter** for its neutral, highly legible character.

- **Contrast Control:** In light mode, avoid pure black for body text. Use `text-primary` for headlines and `text-secondary` for long-form reading to reduce eye strain.
- **Hierarchy:** Use the weight of the font to signify importance. `display-lg` and `headline-lg` should use Bold (700) or Semi-Bold (600) to anchor the page. 
- **Scale:** On mobile devices, large headlines should scale down to the `mobile` variant to ensure they don't break across too many lines.

## Layout & Spacing

The layout utilizes a **Fluid Grid** that prioritizes white space to facilitate better information retention.

- **Grid System:** A 12-column grid with 24px gutters. On desktop, the main content area should be constrained to a 1440px max-width and centered.
- **Breakpoints:**
    - **Desktop (1024px+):** Fixed 280px sidebar. Large 32px margins.
    - **Tablet (768px - 1023px):** Sidebar collapses to an icon-only rail (80px). 24px margins.
    - **Mobile (<768px):** Single column. Sidebar becomes a bottom navigation bar or a top-level burger menu. 16px margins.
- **Rhythm:** All vertical spacing must be a multiple of the 8px `base` unit. Section headers should be separated from content by 40px (`lg`) to create a clear visual break.

## Elevation & Depth

In the light mode variant, depth is communicated through **Translucency** and **Tonal Tiers** rather than heavy shadows.

- **Z-Index 0 (Base):** White (#FFFFFF). The primary canvas.
- **Z-Index 1 (Structural):** Very light purple-grey (#F8F7FF). Used for sidebars and background containers to create a subtle "inset" look.
- **Z-Index 2 (Interactive):** Glassmorphism. Components like modals or floating menus use a backdrop blur of 16px, a white fill at 70% opacity, and a thin 1px border (#E2E8F0).
- **Outlines:** Instead of shadows, use 1px solid borders (#F1F5F9) for cards. On hover, increase the border contrast or add a very soft, high-diffusion shadow (0px 10px 30px rgba(0,0,0,0.04)).

## Shapes

The shape language is defined by "Substantial Softness."

- **Cards:** Use a consistent 18px-20px radius for all primary containers and educational cards.
- **Buttons:** Use a 12px radius for standard buttons to distinguish them from the larger container shapes.
- **Pills:** All chips, tags, and AI chat bubbles should use a fully rounded (pill) shape to emphasize a friendly, conversational tone.

## Components

### Buttons
- **Primary:** Full gradient background with white text. Apply a subtle 2px inner-shadow on top to give a tactile, "pressed" feeling.
- **Secondary:** White background with a 1px gradient border.
- **Ghost:** `text-primary` or gradient text with no background.

### Cards
- **Standard:** White background, 1px light grey border (#F1F5F9), 20px radius.
- **Interactive:** On hover, the border transitions to the primary blue, and a very soft 4% opacity shadow appears.

### Input Fields
- **Chat Bar:** Light lavender-grey background (#F1F0FB), 12px radius, no border by default. On focus, a 1px gradient border appears with a subtle outer glow.

### AI Chat Bubbles
- **User:** Primary gradient background with white text, right-aligned.
- **AI (Dexter):** Solid `surface-subtle` background with `text-primary`, left-aligned.

### Chips & Badges
- Used for subject tagging. Use a high-transparency version of the domain color (10% opacity) for the background and the full-saturation domain color for the text and icons.

### Icons
- Icons should be 24x24px with a 1.5px stroke weight. In light mode, use `text-secondary` for default states and the primary gradient for active or highlighted icons.