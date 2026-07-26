/**
 * Unsupported client detection and fallback
 * Determines if running in a supported Telegram WebApp context or requires deterministic fallback
 */

export type ClientSupportStatus =
  | 'full-telegram-support'
  | 'partial-telegram-support'
  | 'no-telegram-support';

export interface ClientCapabilities {
  status: ClientSupportStatus;
  hasThemeSupport: boolean;
  hasSafeAreaSupport: boolean;
  hasViewportSupport: boolean;
  hasHapticFeedback: boolean;
  hasClosingConfirmation: boolean;
  webAppVersion: string | null;
  platform: string | null;
}

export class ClientDetector {
  private capabilities: ClientCapabilities;

  constructor() {
    this.capabilities = this.detectCapabilities();
  }

  private detectCapabilities(): ClientCapabilities {
    if (typeof window === 'undefined' || !window.Telegram?.WebApp) {
      return {
        status: 'no-telegram-support',
        hasThemeSupport: false,
        hasSafeAreaSupport: false,
        hasViewportSupport: false,
        hasHapticFeedback: false,
        hasClosingConfirmation: false,
        webAppVersion: null,
        platform: null
      };
    }

    const webApp = window.Telegram.WebApp;
    const version = webApp.version || null;
    const platform = webApp.platform || null;

    const hasThemeSupport = !!webApp.themeParams && !!webApp.colorScheme;
    const hasSafeAreaSupport = typeof webApp.safeAreaInsets === 'object';
    const hasViewportSupport = typeof webApp.viewportHeight === 'number';
    const hasHapticFeedback = typeof webApp.HapticFeedback === 'object';
    const hasClosingConfirmation = typeof webApp.enableClosingConfirmation === 'function';

    const supportedFeatures = [
      hasThemeSupport,
      hasSafeAreaSupport,
      hasViewportSupport,
      hasHapticFeedback,
      hasClosingConfirmation
    ].filter(Boolean).length;

    const status: ClientSupportStatus =
      supportedFeatures >= 4
        ? 'full-telegram-support'
        : supportedFeatures >= 1
          ? 'partial-telegram-support'
          : 'no-telegram-support';

    return {
      status,
      hasThemeSupport,
      hasSafeAreaSupport,
      hasViewportSupport,
      hasHapticFeedback,
      hasClosingConfirmation,
      webAppVersion: version,
      platform
    };
  }

  public getCapabilities(): ClientCapabilities {
    return this.capabilities;
  }

  public isSupported(): boolean {
    return (
      this.capabilities.status === 'full-telegram-support' ||
      this.capabilities.status === 'partial-telegram-support'
    );
  }

  public requiresFallback(): boolean {
    return this.capabilities.status === 'no-telegram-support';
  }

  public getFallbackReason(): string {
    if (!this.capabilities.requiresFallback()) {
      return '';
    }

    return 'Telegram WebApp API is not available. Using deterministic fallback theme for test builds.';
  }

  public getVersion(): string | null {
    return this.capabilities.webAppVersion;
  }

  public getPlatform(): string | null {
    return this.capabilities.platform;
  }

  public hasMinimumVersion(minVersion: string): boolean {
    if (!this.capabilities.webAppVersion) {
      return false;
    }

    const currentParts = this.capabilities.webAppVersion.split('.').map(Number);
    const minParts = minVersion.split('.').map(Number);

    for (let i = 0; i < Math.max(currentParts.length, minParts.length); i++) {
      const current = currentParts[i] ?? 0;
      const min = minParts[i] ?? 0;

      if (current > min) return true;
      if (current < min) return false;
    }

    return true;
  }
}