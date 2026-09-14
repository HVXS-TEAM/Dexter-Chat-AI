---
name: Aether Intelligence Light
colors:
  surface: '#fcf8ff'
  surface-dim: '#F9FAFB'
  surface-bright: '#FFFFFF'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f2ff'
  surface-container: '#f0ecf9'
  surface-container-high: '#eae6f4'
  surface-container-highest: '#e4e1ee'
  on-surface: '#111827'
  on-surface-variant: '#4B5563'
  inverse-surface: '#302f39'
  inverse-on-surface: '#f3effc'
  outline: '#E5E7EB'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#4648d4'
  on-secondary: '#ffffff'
  secondary-container: '#6063ee'
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
  secondary-fixed: '#e1e0ff'
  secondary-fixed-dim: '#c0c1ff'
  on-secondary-fixed: '#07006c'
  on-secondary-fixed-variant: '#2f2ebe'
  tertiary-fixed: '#ffdbcc'
  tertiary-fixed-dim: '#ffb695'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7b2f00'
  background: '#fcf8ff'
  on-background: '#1b1b24'
  surface-variant: '#e4e1ee'
  gradient-start: '#4F46E5'
  gradient-end: '#9333EA'
  domain-green: '#059669'
  domain-blue: '#2563EB'
  domain-orange: '#EA580C'
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

The design system evolves from a dark, atmospheric environment into a **Prismatic Minimalist** experience. It maintains the core identity of "focused intelligence" but shifts from "midnight depth" to "luminous clarity." The target audience remains high-performing students and professionals, now supported by an interface that feels like a clean, well-lit workspace.

The aesthetic direction is **Refined Glassmorphism** on a **High-Contrast White** base. By utilizing "Paper-White" surfaces and vibrant gradient accents, the UI evokes a sense of premium precision.

Key attributes include:
- **Luminous Clarity:** Utilizing pure white backgrounds and very light grey containers to maximize legibility and reduce cognitive load.
- **Prismatic Accents:** The signature blue-to-purple gradient remains the focal point for action, representing the "spark" of AI intelligence within a clean canvas.
- **Structured Modernism:** Relying on precise typography and intentional whitespace rather than heavy shadows to define hierarchy.
- **Approachable Sophistication:** Retaining the generous 18px-20px border radii to ensure the advanced technology feels inviting and human-centric.

## Colors

This light mode adaptation focuses on high-key foundations while preserving the brand's energetic spirit through gradients.

- **Foundations:** The primary background is pure white (#FFFFFF). Surface tiers are created using subtle increments of cool grey (e.g., #F9FAFB and #F3F4F6) to maintain a clean, clinical feel without becoming stark.
- **The Intelligence Gradient:** The signature Blue-to-Purple gradient is the primary interaction driver. It is used for primary buttons, active navigation states, and progress indicators.
- **Domain Indicators:** Semantic colors (Green, Blue, Orange) are adjusted for higher saturation and lower lightness to ensure accessibility and "pop" against light surfaces.
- **Typography & Neutrals:** Headlines utilize a deep near-black (#111827) for maximum contrast, while body text uses a slightly softened slate (#374151) to improve long-form reading comfort.

## Typography

The typography continues to rely on **Inter** for its neutral, highly legible, and "system-native" characteristics.

- **Hierarchy:** Contrast is achieved through weight and color rather than just size. Headlines use the darkest neutral (#111827), while metadata and secondary labels use mid-tone greys (#6B7280).
- **Legibility:** On light backgrounds, the regular weight (400) provides excellent clarity. For emphasized "AI-generated" content, consider using a slightly tighter line height or the medium (500) weight to distinguish it from standard system text.
- **Scale:** The scale remains tight to support data-heavy educational tools, ensuring that complex lessons can be viewed with minimal scrolling on desktop.

## Layout & Spacing

The layout follows a **Fluid Grid** model with a hard max-width to ensure readability on ultra-wide displays.

- **Grid:** A 12-column system with 24px gutters. Margins are fixed at 32px for desktop, scaling down to 16px for mobile.
- **The Sidebar:** The 280px left sidebar is visually separated from the main stage by a subtle #E5E7EB border or a very light #F9FAFB background tint.
- **Rhythm:** All spacing is derived from a base-8 unit. Use 24px for component internals and 40px+ for major section separation to create a "breathable" learning environment.

## Elevation & Depth

In Light Mode, depth is communicated through **Subtle Borders** and **Soft Ambient Shadows** rather than the tonal layering used in the dark theme.

- **Z-Index 0 (Base):** White (#FFFFFF).
- **Z-Index 1 (Surfaces):** Lightest Grey (#F9FAFB) with a 1px border (#E5E7EB). Used for sidebars and secondary content modules.
- **Z-Index 2 (Interactive):** Glassmorphism is applied to floating menus and modals using a backdrop blur (12px), 40% white fill, and a very soft, high-diffusion shadow (0px 10px 30px rgba(0,0,0,0.04)).
- **Outlines:** Most cards use a 1px solid border (#E5E7EB) instead of a shadow to maintain a clean, organized aesthetic.

## Shapes

The shape language remains "Substantial Softness."

- **Containers:** Large containers and cards use an **18px (rounded-xl)** radius to create a modern, high-end feel.
- **Interactive Elements:** Buttons and inputs use a **12px (rounded-md)** radius.
- **Pills:** Status badges and chips use a **9999px (full)** radius to contrast against the more geometric container shapes.

## Components

### Buttons
- **Primary:** Background gradient (Blue #4F46E5 to Purple #9333EA), white text.
- **Secondary:** White background with 1px light grey border (#E5E7EB). Hover state adds a subtle shadow.
- **Icon Buttons:** No background, using the brand-blue for the icon color.

### Cards
- **Standard:** White background, 1px border (#E5E7EB), 18px radius.
- **Active/Featured:** 1px gradient border or a subtle domain-color glow.

### Input Fields
- **Search & Chat:** Very light grey background (#F3F4F6), 12px radius, no border. On focus, the background turns white and gains a 1px gradient border.

### AI Chat Bubbles
- **User:** White background with a 1px border (#E5E7EB), right-aligned.
- **AI:** Light lavender or blue-tinted background (#EFF6FF), left-aligned, featuring the robot head icon.

### Chips & Badges
- Used for subject tags. These feature a low-opacity version of the domain color (10% opacity fill) with full-opacity text of the same hue.