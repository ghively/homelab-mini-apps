/**
 * Web Components index
 * Exports all custom elements for design system usage
 */

export { DesignSystemElement } from './base.js';
export { ThemeAwareElement } from './theme-aware.js';
export { SafeAreaWrapper } from './safe-area.js';
export { FocusTrap } from './focus-trap.js';
export { UnsupportedClientBanner } from './unsupported-client.js';

export { ThemeProvider } from '../theme/provider.js';
export { SafeAreaProvider } from '../safe-area/provider.js';
export { AccessibilityProvider } from '../accessibility/provider.js';
export { ClientDetector } from '../client/detector.js';

export type { ThemeChangeListener, ThemeProviderOptions } from '../theme/provider.js';
export type {
  SafeAreaInsets,
  ViewportData
} from '../safe-area/provider.js';
export type {
  ReducedMotionState,
  AccessibilityState
} from '../accessibility/provider.js';
export type {
  ClientSupportStatus,
  ClientCapabilities
} from '../client/detector.js';