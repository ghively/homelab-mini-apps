/**
 * Safe area primitives for Telegram Mini Apps
 * Handles content-safe-area and viewport-stable-height
 */

export interface SafeAreaInsets {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export interface ViewportData {
  height: number;
  width: number;
  stableHeight: number;
  isExpanded: boolean;
  safeAreaInsets: SafeAreaInsets;
}

export class SafeAreaProvider {
  private currentInsets: SafeAreaInsets;
  private currentViewport: ViewportData;
  private isTelegramAvailable: boolean;

  constructor() {
    this.isTelegramAvailable = this.detectTelegram();
    this.currentInsets = this.initializeInsets();
    this.currentViewport = this.initializeViewport();

    if (this.isTelegramAvailable) {
      this.setupListeners();
    }
  }

  private detectTelegram(): boolean {
    return typeof window !== 'undefined' && !!window.Telegram?.WebApp;
  }

  private initializeInsets(): SafeAreaInsets {
    if (!this.isTelegramAvailable) {
      return { top: 0, right: 0, bottom: 0, left: 0 };
    }

    const webApp = window.Telegram!.WebApp;
    return {
      top: webApp.safeAreaInsets?.top ?? 0,
      right: webApp.safeAreaInsets?.right ?? 0,
      bottom: webApp.safeAreaInsets?.bottom ?? 0,
      left: webApp.safeAreaInsets?.left ?? 0
    };
  }

  private initializeViewport(): ViewportData {
    if (!this.isTelegramAvailable) {
      const height = window.innerHeight;
      const width = window.innerWidth;
      return {
        height,
        width,
        stableHeight: height,
        isExpanded: false,
        safeAreaInsets: this.currentInsets
      };
    }

    const webApp = window.Telegram!.WebApp;
    return {
      height: webApp.viewportHeight,
      width: webApp.viewportWidth,
      stableHeight: webApp.viewportStableHeight,
      isExpanded: webApp.isExpanded,
      safeAreaInsets: this.currentInsets
    };
  }

  private setupListeners(): void {
    if (!window.Telegram?.WebApp) return;

    const webApp = window.Telegram.WebApp;

    webApp.onEvent('viewportChanged', () => {
      this.currentViewport = {
        height: webApp.viewportHeight,
        width: webApp.viewportWidth,
        stableHeight: webApp.viewportStableHeight,
        isExpanded: webApp.isExpanded,
        safeAreaInsets: {
          top: webApp.safeAreaInsets?.top ?? 0,
          right: webApp.safeAreaInsets?.right ?? 0,
          bottom: webApp.safeAreaInsets?.bottom ?? 0,
          left: webApp.safeAreaInsets?.left ?? 0
        }
      };
    });
  }

  public getSafeAreaInsets(): SafeAreaInsets {
    return this.currentInsets;
  }

  public getViewportData(): ViewportData {
    return this.currentViewport;
  }

  public getStableHeight(): number {
    return this.currentViewport.stableHeight;
  }

  public getContentSafeArea(): {
    top: number;
    right: number;
    bottom: number;
    left: number;
  } {
    return this.currentInsets;
  }

  public expand(): void {
    if (this.isTelegramAvailable && window.Telegram?.WebApp) {
      window.Telegram.WebApp.expand();
    }
  }

  public isTelegramContext(): boolean {
    return this.isTelegramAvailable;
  }

  destroy(): void {
    if (this.isTelegramAvailable && window.Telegram?.WebApp) {
      window.Telegram.WebApp.offEvent('viewportChanged', () => {});
    }
  }
}