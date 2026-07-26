# Design System Implementation Plan

## Scope

Implement a small TypeScript/Vite web-component design-system and theming slice:
- Semantic tokens with Telegram light/dark theme parameter mapping
- Telegram theme change events
- Safe-area/content-safe-area/viewport-stable-height primitives
- Accessible navigation/focus/contrast/reduced-motion states
- Unsupported-client state
- Deterministic browser fallback for test builds

## Architecture

### Core Modules

1. **Types** (`src/types/telegram.ts`)
   - `TelegramThemeParams`: WebApp theme parameter interface
   - `TelegramColorScheme`: 'light' | 'dark'
   - `TelegramWebApp`: WebApp API contract
   - `ThemeChangeEvent`: Theme update event payload

2. **Tokens** (`src/tokens/`)
   - `telegram-themes.ts`: TELEGRAM_LIGHT_THEME, TELEGRAM_DARK_THEME, FALLBACK_THEME
   - `semantic.ts`: deriveSemanticTokens() function, SemanticTokens interface

3. **Providers** (`src/*/provider.ts`)
   - `theme/provider.ts`: ThemeProvider class with change event support
   - `safe-area/provider.ts`: SafeAreaProvider for viewport/safe-area
   - `accessibility/provider.ts`: AccessibilityProvider for reduced-motion/focus
   - `client/detector.ts`: ClientDetector for capability detection

4. **Web Components** (`src/web-components/`)
   - `base.ts`: DesignSystemElement base class
   - `theme-aware.ts`: ThemeAwareElement with CSS custom properties
   - `safe-area.ts`: <ds-safe-area> custom element
   - `focus-trap.ts`: <ds-focus-trap> for keyboard navigation
   - `unsupported-client.ts`: <ds-unsupported-client-banner>

## Test Coverage

### Unit Tests
- Theme provider initialization, light/dark theme handling, change events
- Safe area initialization, viewport changes, Telegram context detection
- Accessibility state, reduced motion, focus visibility
- Client detector, version checking, capability detection
- Semantic token derivation, contrast validation

### Component Tests
- <ds-safe-area> CSS variables, expand-on-mount, viewport updates
- <ds-unsupported-client-banner> display logic, message customization
- Focus trap keyboard navigation, focus management

### Browser Tests
- Light/dark theme switching
- Safe area/viewport change events
- Keyboard focus and reduced motion states
- Unsupported client banner visibility

## Acceptance Criteria

✅ Unit/component/browser tests cover:
  - Light/dark updates
  - Safe-area/viewport changes
  - Keyboard focus
  - Unsupported client
  - Fallback mode

✅ Production bundle builds reproducibly from lockfile

✅ Dependency inventory/license/activity/security gate captured

✅ Committed non-protected branch

✅ No merge/push/deploy

## Artifacts

- `/packages/design-system/` - Full TypeScript/Vite package
- `/packages/design-system/src/` - Source code
- `/packages/design-system/tests/` - Test suite
- `/packages/design-system/dist/` - Production build
- `/artifacts/miniapps-kanban/t_039dc360/handoff.json` - Completion evidence