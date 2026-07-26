import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ThemeProvider } from '../src/theme/provider.js';
import type { TelegramThemeParams, TelegramColorScheme, ThemeChangeEvent } from '../src/types/telegram.js';
import { deriveSemanticTokens, TELEGRAM_LIGHT_THEME, TELEGRAM_DARK_THEME } from '../src/tokens/semantic.js';
import { TELEGRAM_LIGHT_THEME as FALLBACK_LIGHT, TELEGRAM_DARK_THEME as FALLBACK_DARK } from '../src/tokens/telegram-themes.js';

describe('ThemeProvider', () => {
  let mockWebApp: any;
  let mockThemeParams: TelegramThemeParams;
  let mockColorScheme: TelegramColorScheme;

  beforeEach(() => {
    mockThemeParams = {
      bg_color: '#ffffff',
      text_color: '#000000',
      hint_color: '#707579',
      link_color: '#3390ec',
      button_color: '#3390ec',
      button_text_color: '#ffffff',
      secondary_bg_color: '#f4f4f5',
      header_bg_color: '#ffffff',
      section_bg_color: '#ffffff',
      section_header_text_color: '#616d76',
      subtitle_text_color: '#707579',
      destructive_text_color: '#e53935'
    };
    mockColorScheme = 'light';

    mockWebApp = {
      themeParams: mockThemeParams,
      colorScheme: mockColorScheme,
      isVersionAtLeast: vi.fn((version: string) => true),
      onEvent: vi.fn(),
      offEvent: vi.fn()
    };

    (global as any).window = {
      Telegram: { WebApp: mockWebApp }
    };
  });

  afterEach(() => {
    delete (global as any).window;
  });

  describe('initialization', () => {
    it('should initialize with Telegram WebApp theme', () => {
      const provider = new ThemeProvider({ webApp: mockWebApp });
      const theme = provider.getCurrentTheme();

      expect(theme.colors.background.primary).toBe('#ffffff');
      expect(theme.colors.text.primary).toBe('#000000');
      expect(theme.colorScheme).toBe('light');
    });

    it('should use fallback theme when WebApp unavailable', () => {
      delete (global as any).window;
      const provider = new ThemeProvider();
      const theme = provider.getCurrentTheme();

      expect(theme.colors.background.primary).toBe(FALLBACK_LIGHT.bg_color);
      expect(theme.colorScheme).toBe('light');
    });

    it('should detect Telegram WebApp availability', () => {
      const provider = new ThemeProvider({ webApp: mockWebApp });
      expect(provider.isTelegramAvailable()).toBe(true);
    });

    it('should report unavailable when no WebApp', () => {
      delete (global as any).window;
      const provider = new ThemeProvider();
      expect(provider.isTelegramAvailable()).toBe(false);
    });
  });

  describe('theme updates', () => {
    it('should notify listeners on theme change', () => {
      const provider = new ThemeProvider({ webApp: mockWebApp });
      const listener = vi.fn();
      provider.addListener(listener);

      const newThemeParams: TelegramThemeParams = {
        ...mockThemeParams,
        bg_color: '#1c1c1d',
        text_color: '#ffffff'
      };

      mockWebApp.themeParams = newThemeParams;
      mockWebApp.colorScheme = 'dark';

      const themeChangeCallback = mockWebApp.onEvent.mock.calls.find(
        (call: any[]) => call[0] === 'themeChanged'
      )?.[1];

      if (themeChangeCallback) {
        themeChangeCallback();
      }

      expect(listener).toHaveBeenCalled();
      expect(listener.mock.calls[0][0].colorScheme).toBe('dark');
    });

    it('should update current theme after change event', () => {
      const provider = new ThemeProvider({ webApp: mockWebApp });
      const listener = vi.fn();
      provider.addListener(listener);

      mockWebApp.themeParams = {
        bg_color: '#1c1c1d',
        text_color: '#ffffff',
        hint_color: '#aaaaaa',
        link_color: '#64b5ef',
        button_color: '#2ea5ff',
        button_text_color: '#ffffff'
      };
      mockWebApp.colorScheme = 'dark';

      const themeChangeCallback = mockWebApp.onEvent.mock.calls.find(
        (call: any[]) => call[0] === 'themeChanged'
      )?.[1];

      if (themeChangeCallback) {
        themeChangeCallback();
      }

      const updatedTheme = provider.getCurrentTheme();
      expect(updatedTheme.colorScheme).toBe('dark');
      expect(updatedTheme.colors.background.primary).toBe('#1c1c1d');
      expect(updatedTheme.colors.text.primary).toBe('#ffffff');
    });

    it('should unsubscribe listener correctly', () => {
      const provider = new ThemeProvider({ webApp: mockWebApp });
      const listener = vi.fn();
      const unsubscribe = provider.addListener(listener);

      unsubscribe();

      mockWebApp.themeParams = { bg_color: '#ff0000' };
      mockWebApp.colorScheme = 'dark';

      const themeChangeCallback = mockWebApp.onEvent.mock.calls.find(
        (call: any[]) => call[0] === 'themeChanged'
      )?.[1];

      if (themeChangeCallback) {
        themeChangeCallback();
      }

      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('dark theme support', () => {
    it('should handle dark theme parameters', () => {
      const darkThemeParams = FALLBACK_DARK;
      const provider = new ThemeProvider({
        webApp: {
          ...mockWebApp,
          themeParams: darkThemeParams,
          colorScheme: 'dark'
        }
      });

      const theme = provider.getCurrentTheme();
      expect(theme.colorScheme).toBe('dark');
      expect(theme.colors.background.primary).toBe(darkThemeParams.bg_color);
      expect(theme.colors.text.primary).toBe(darkThemeParams.text_color);
    });
  });

  describe('version checking', () => {
    it('should check WebApp version', () => {
      mockWebApp.isVersionAtLeast = vi.fn((version: string) => version <= '6.9');
      const provider = new ThemeProvider({ webApp: mockWebApp });

      expect(provider.isVersionAtLeast('6.0')).toBe(true);
      expect(provider.isVersionAtLeast('7.0')).toBe(false);
    });

    it('should return false when no WebApp', () => {
      delete (global as any).window;
      const provider = new ThemeProvider();

      expect(provider.isVersionAtLeast('6.0')).toBe(false);
    });
  });

  describe('cleanup', () => {
    it('should remove event listeners on destroy', () => {
      const provider = new ThemeProvider({ webApp: mockWebApp });
      provider.destroy();

      expect(mockWebApp.offEvent).toHaveBeenCalled();
    });

    it('should clear all listeners on destroy', () => {
      const provider = new ThemeProvider({ webApp: mockWebApp });
      const listener = vi.fn();
      provider.addListener(listener);

      provider.destroy();

      mockWebApp.themeParams = { bg_color: '#ff0000' };
      mockWebApp.colorScheme = 'dark';

      const themeChangeCallback = mockWebApp.onEvent.mock.calls.find(
        (call: any[]) => call[0] === 'themeChanged'
      )?.[1];

      if (themeChangeCallback) {
        themeChangeCallback();
      }

      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('static factory', () => {
    it('should create default provider without change events', () => {
      const provider = ThemeProvider.createDefault();

      expect(provider.isTelegramAvailable()).toBe(false);
      expect(mockWebApp.onEvent).not.toHaveBeenCalled();
    });
  });
});