---
name: Aether Intelligence
colors:
  surface: '#13121b'
  surface-dim: '#13121b'
  surface-bright: '#393842'
  surface-container-lowest: '#0e0d16'
  surface-container-low: '#1b1b24'
  surface-container: '#1f1f28'
  surface-container-high: '#2a2933'
  surface-container-highest: '#35343e'
  on-surface: '#e4e1ee'
  on-surface-variant: '#c7c4d8'
  inverse-surface: '#e4e1ee'
  inverse-on-surface: '#302f39'
  outline: '#918fa1'
  outline-variant: '#464555'
  surface-tint: '#c3c0ff'
  primary: '#c3c0ff'
  on-primary: '#1d00a5'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#4d44e3'
  secondary: '#bcc7de'
  on-secondary: '#263143'
  secondary-container: '#3e495d'
  on-secondary-container: '#aeb9d0'
  tertiary: '#ffb695'
  on-tertiary: '#571f00'
  tertiary-container: '#a44100'
  on-tertiary-container: '#ffd2be'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#d8e3fb'
  secondary-fixed-dim: '#bcc7de'
  on-secondary-fixed: '#111c2d'
  on-secondary-fixed-variant: '#3c475a'
  tertiary-fixed: '#ffdbcc'
  tertiary-fixed-dim: '#ffb695'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7b2f00'
  background: '#13121b'
  on-background: '#e4e1ee'
  surface-variant: '#35343e'
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

The design system is engineered to evoke a sense of focused intelligence, futuristic reliability, and scholarly depth. It targets a modern student and professional audience who value efficiency and advanced AI capabilities.

The aesthetic direction is **Modern Glassmorphism** layered over a deep **Midnight Minimalism**. It balances high-tech iridescent accents with a very dark, low-distraction environment. 

Key attributes include:
- **Atmospheric Depth:** Utilizing deep midnight blues and subtle blurs to create a spatial, "endless" learning environment.
- **Iridescent Energy:** Vibrant gradients represent the flow of AI-driven information.
- **High-Fidelity Precision:** Sharp typography and generous spacing ensure complex educational data remains digestible.
- **Humanistic Tech:** Softened by large border radii (16-20px) to make the advanced AI feel approachable rather than clinical.

## Colors

The palette is anchored in a true dark-mode experience. 

- **Foundations:** The base background is a strict Midnight Blue (#0B0E14). Surfaces utilize a slightly lighter, blue-tinted dark grey to provide depth without breaking the immersion.
- **Accents:** The primary interaction color is an iridescent gradient flowing from electric blue to deep violet. This gradient should be used sparingly for high-value actions (Primary Buttons, Active States, Logo accents).
- **Domain Indicators:** Use the semantic secondary accents to categorize content. These should be applied to category icons, progress bars, and subtle card borders within specific learning modules.
- **Neutrals:** Use low-contrast greys for secondary text to maintain a calm visual hierarchy.

## Typography

The design system uses **Inter** exclusively to provide a clean, "system-native" feel that prioritizes legibility in complex educational interfaces.

- **Scale:** A tight scale is used to ensure high information density on desktop screens while maintaining a clear hierarchy.
- **Weight:** Bold weights (600-700) are reserved for key navigational headers and brand moments. Regular weight (400) is used for body copy to reduce eye strain in dark mode.
- **Contrast:** Ensure a significant contrast ratio between Headlines (White #FFFFFF) and Body copy (Slate #94A3B8) to guide the user's eye naturally.

## Layout & Spacing

The layout is based on a **Fluid Grid** with fixed constraints for desktop viewing.

- **Grid Model:** 12-column system with 24px gutters. The layout should center itself on extra-wide monitors with a max-width of 1440px.
- **Sidebar:** Navigation is housed in a fixed-width left sidebar (280px) to provide quick access to subjects and chat history.
- **Rhythm:** An 8px base unit drives all padding and margin decisions. Use 24px (md) for standard component spacing and 40px (lg) for section separation.
- **Density:** Educational content (lessons/quizzes) should use a "Comfortable" density, whereas the Dashboard and Chat interfaces use "Compact" density to maximize available context.

## Elevation & Depth

This design system eschews traditional shadows in favor of **Tonal Layering** and **Glassmorphism**.

- **Z-Index 0 (Background):** #0B0E14. The solid base.
- **Z-Index 1 (Surfaces):** #111827. Used for sidebar, main content containers, and secondary cards.
- **Z-Index 2 (Interactive):** Glassmorphic surfaces. Use a background blur of 12px-20px with a 10% white stroke and 5% white fill. This is reserved for modals, floating action menus, and active chat bubbles.
- **Outlines:** Use subtle 1px borders (#1F2937) for card definitions instead of shadows to maintain a "flat-but-deep" aesthetic.

## Shapes

The shape language is "Substantial Softness." 

- **Large Radii:** Standard cards and containers use an 18px radius to feel modern and friendly.
- **Interactive Elements:** Buttons and input fields use a slightly tighter 12px radius to signify their functional nature.
- **Icons:** All icons must be native inline SVGs with a stroke width of 1.5px and rounded caps/joins to match the typography's character. Never use icon fonts.

## Components

### Buttons
- **Primary:** Gradient background (Blue to Violet), white text. Subtle hover state: 10% brightness increase.
- **Secondary:** Surface-tinted background with a 1px iridescent border.
- **Ghost:** No background, iridescent text or white text depending on context.

### Cards
- **Standard Card:** Background #111827, 18px radius, 1px border (#1F2937).
- **Subject Card:** Features a small circular icon at the top left using the domain-specific color (e.g., Green for Eco) and a 1px colored glow on hover.

### Input Fields
- **Search/Chat Bar:** Darker background than the surface (#09090B), 12px radius, left-aligned SVG icon. On focus, the border should glow with the primary gradient.

### AI Chat Bubbles
- **User:** Glassmorphic translucent surface, right-aligned.
- **AI (Dexter):** Solid surface (#1E293B), left-aligned, accompanied by the robot head icon (sourced from IMAGE_2).

### Chips & Badges
- Used for "Subject Tags" or "Difficulty Levels." Small caps (label-sm), 100px pill radius, low-opacity background of the domain color.

### Icons
- **Strict Requirement:** Icons must be authored as 24x24px viewbox SVGs. Use `currentColor` for fills/strokes to ensure they adapt to theme tokens.