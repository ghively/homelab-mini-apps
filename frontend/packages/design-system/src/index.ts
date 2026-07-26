/**
 * Design system package index
 * Exports tokens, providers, and web components
 */

export type {
  TelegramThemeParams,
  TelegramColorScheme,
  TelegramWebApp,
  ThemeChangeEvent
} from './types/telegram.js';

export {
  TELEGRAM_LIGHT_THEME,
  TELEGRAM_DARK_THEME,
  FALLBACK_THEME
} from './tokens/telegram-themes.js';

export {
  deriveSemanticTokens,
  type SemanticTokens
} from './tokens/semantic.js';

export {
  ThemeProvider,
  type ThemeChangeListener,
  type ThemeProviderOptions
} from './theme/provider.js';

export {
  SafeAreaProvider,
  type SafeAreaInsets,
  type ViewportData
} from './safe-area/provider.js';

export {
  AccessibilityProvider,
  type ReducedMotionState,
  type AccessibilityState
} from './accessibility/provider.js';

export {
  ClientDetector,
  type ClientSupportStatus,
  type ClientCapabilities
} from './client/detector.js';