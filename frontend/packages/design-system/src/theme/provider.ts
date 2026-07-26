/**
 * Theme provider for Telegram WebApp theming
 * Manages theme initialization, updates, and change events
 */

import type {
  TelegramThemeParams,
  TelegramColorScheme,
  TelegramWebApp,
  ThemeChangeEvent
} from '../types/telegram.js';
import { TELEGRAM_LIGHT_THEME, TELEGRAM_DARK_THEME, FALLBACK_THEME } from '../tokens/telegram-themes.js';
import { deriveSemanticTokens, SemanticTokens } from '../tokens/semantic.js';

export type ThemeChangeListener = (event: ThemeChangeEvent) => void;

export interface ThemeProviderOptions {
  webApp?: TelegramWebApp;
  enableChangeEvents?: boolean;
}

export class ThemeProvider {
  private webApp: TelegramWebApp | null;
  private listeners: Set<ThemeChangeListener> = new Set();
  private enableChangeEvents: boolean;
  private currentTheme: SemanticTokens;

  constructor(options: ThemeProviderOptions = {}) {
    this.webApp = options.webApp ?? this.detectWebApp();
    this.enableChangeEvents = options.enableChangeEvents ?? true;
    this.currentTheme = this.initializeTheme();

    if (this.webApp && this.enableChangeEvents) {
      this.setupChangeListeners();
    }
  }

  private detectWebApp(): TelegramWebApp | null {
    if (typeof window === 'undefined' || !window.Telegram?.WebApp) {
      return null;
    }
    return window.Telegram.WebApp;
  }

  private initializeTheme(): SemanticTokens {
    if (this.webApp) {
      const themeParams = this.webApp.themeParams || {};
      const colorScheme = this.webApp.colorScheme || 'light';
      return deriveSemanticTokens(themeParams, colorScheme);
    }

    return deriveSemanticTokens(FALLBACK_THEME, 'light');
  }

  private setupChangeListeners(): void {
    if (!this.webApp) return;

    const handleThemeChanged = () => {
      const themeParams = this.webApp!.themeParams || {};
      const colorScheme = this.webApp!.colorScheme || 'light';
      const newTheme = deriveSemanticTokens(themeParams, colorScheme);
      this.currentTheme = newTheme;

      const event: ThemeChangeEvent = { themeParams, colorScheme };
      this.notifyListeners(event);
    };

    this.webApp.onEvent('themeChanged', handleThemeChanged);
  }

  public getCurrentTheme(): SemanticTokens {
    return this.currentTheme;
  }

  public addListener(listener: ThemeChangeListener): () => void {
    this.listeners.add(listener);
    return () => this.removeListener(listener);
  }

  public removeListener(listener: ThemeChangeListener): void {
    this.listeners.delete(listener);
  }

  private notifyListeners(event: ThemeChangeEvent): void {
    this.listeners.forEach((listener) => {
      try {
        listener(event);
      } catch (error) {
        console.error('Theme change listener error:', error);
      }
    });
  }

  public isTelegramAvailable(): boolean {
    return this.webApp !== null;
  }

  public isVersionAtLeast(version: string): boolean {
    if (!this.webApp) return false;
    return this.webApp.isVersionAtLeast(version);
  }

  public destroy(): void {
    if (this.webApp && this.enableChangeEvents) {
      this.webApp.offEvent('themeChanged', () => {});
    }
    this.listeners.clear();
  }

  static createDefault(): ThemeProvider {
    return new ThemeProvider({ enableChangeEvents: false });
  }
}