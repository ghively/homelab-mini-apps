# @homelab-telegram-miniapps/design-system

Telegram-native design system with theming primitives for Mini Apps.

## Features

- **Semantic Tokens**: Telegram light/dark theme parameter mapping with fallback
- **Theme Provider**: Reacts to Telegram WebApp theme change events
- **Safe Area Primitives**: Content-safe-area and viewport-stable-height constraints
- **Accessibility**: Reduced-motion, focus management, and contrast states
- **Unsupported Client Detection**: Deterministic browser fallback for test builds
- **Web Components**: `<ds-safe-area>`, `<ds-unsupported-client-banner>`, `<ds-focus-trap>`

## Installation

```bash
npm install @homelab-telegram-miniapps/design-system
```

## Usage

### Using the theme provider

```typescript
import { ThemeProvider } from '@homelab-telegram-miniapps/design-system';

const themeProvider = new ThemeProvider();
const theme = themeProvider.getCurrentTheme();

themeProvider.addListener((event) => {
  console.log('Theme changed to:', event.colorScheme);
});
```

### Using web components

```html
<ds-safe-area expand-on-mount="true">
  <ds-unsupported-client-banner></ds-unsupported-client-banner>
  <!-- Your content here -->
</ds-safe-area>
```

### Importing web components

```typescript
import '@homelab-telegram-miniapps/design-system/web-components';
```

## API

### ThemeProvider

- `getCurrentTheme()`: Get current semantic tokens
- `addListener(listener)`: Subscribe to theme changes
- `isTelegramAvailable()`: Check if running in Telegram WebApp
- `isVersionAtLeast(version)`: Check WebApp version
- `destroy()`: Cleanup listeners

### SafeAreaProvider

- `getSafeAreaInsets()`: Get Telegram safe area insets
- `getViewportData()`: Get viewport dimensions and stable height
- `getContentSafeArea()`: Get content-safe-area values
- `expand()`: Request viewport expansion

### AccessibilityProvider

- `getState()`: Get current accessibility state
- `shouldReduceMotion()`: Check if motion should be reduced
- `addListener(listener)`: Subscribe to state changes

### ClientDetector

- `getCapabilities()`: Get full client capability report
- `isSupported()`: Check if client has Telegram support
- `requiresFallback()`: Check if browser fallback is needed
- `getVersion()`: Get WebApp version
- `hasMinimumVersion(version)`: Check version requirements

## Testing

```bash
npm test              # Run tests
npm run test:ui       # Run tests with UI
npm run test:coverage # Run tests with coverage report
```

## Building

```bash
npm run build         # Build production bundle
```

## License

UNLICENSED