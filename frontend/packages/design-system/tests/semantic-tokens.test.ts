import { describe, it, expect } from 'vitest';
import {
  deriveSemanticTokens,
  type SemanticTokens
} from '../src/tokens/semantic.js';
import { TELEGRAM_LIGHT_THEME, TELEGRAM_DARK_THEME } from '../src/tokens/telegram-themes.js';

describe('Semantic Tokens', () => {
  describe('derivation', () => {
    it('should derive tokens from light theme', () => {
      const tokens = deriveSemanticTokens(TELEGRAM_LIGHT_THEME, 'light');

      expect(tokens.colorScheme).toBe('light');
      expect(tokens.colors.background.primary).toBe('#ffffff');
      expect(tokens.colors.text.primary).toBe('#000000');
      expect(tokens.colors.text.hint).toBe('#707579');
      expect(tokens.colors.text.link).toBe('#3390ec');
      expect(tokens.colors.button.background).toBe('#3390ec');
      expect(tokens.colors.button.text).toBe('#ffffff');
    });

    it('should derive tokens from dark theme', () => {
      const tokens = deriveSemanticTokens(TELEGRAM_DARK_THEME, 'dark');

      expect(tokens.colorScheme).toBe('dark');
      expect(tokens.colors.background.primary).toBe('#1c1c1d');
      expect(tokens.colors.text.primary).toBe('#ffffff');
      expect(tokens.colors.text.hint).toBe('#aaaaaa');
      expect(tokens.colors.text.link).toBe('#64b5ef');
      expect(tokens.colors.button.background).toBe('#2ea5ff');
      expect(tokens.colors.button.text).toBe('#ffffff');
    });

    it('should handle missing theme params with defaults', () => {
      const partialTheme = {
        bg_color: '#ff0000'
      };

      const tokens = deriveSemanticTokens(partialTheme, 'light');

      expect(tokens.colors.background.primary).toBe('#ff0000');
      expect(tokens.colors.text.primary).toBe('#000000');
      expect(tokens.colors.text.hint).toBe('#707579');
    });

    it('should handle empty theme params', () => {
      const tokens = deriveSemanticTokens({}, 'light');

      expect(tokens.colors.background.primary).toBe('#ffffff');
      expect(tokens.colors.text.primary).toBe('#000000');
      expect(tokens.colors.text.hint).toBe('#707579');
    });
  });

  describe('color structure', () => {
    it('should have background color group', () => {
      const tokens = deriveSemanticTokens(TELEGRAM_LIGHT_THEME, 'light');

      expect(tokens.colors.background.primary).toBeDefined();
      expect(tokens.colors.background.secondary).toBeDefined();
      expect(tokens.colors.background.header).toBeDefined();
      expect(tokens.colors.background.section).toBeDefined();
    });

    it('should have text color group', () => {
      const tokens = deriveSemanticTokens(TELEGRAM_LIGHT_THEME, 'light');

      expect(tokens.colors.text.primary).toBeDefined();
      expect(tokens.colors.text.secondary).toBeDefined();
      expect(tokens.colors.text.hint).toBeDefined();
      expect(tokens.colors.text.link).toBeDefined();
      expect(tokens.colors.text.destructive).toBeDefined();
    });

    it('should have button color group', () => {
      const tokens = deriveSemanticTokens(TELEGRAM_LIGHT_THEME, 'light');

      expect(tokens.colors.button.background).toBeDefined();
      expect(tokens.colors.button.text).toBeDefined();
    });

    it('should have section header color', () => {
      const tokens = deriveSemanticTokens(TELEGRAM_LIGHT_THEME, 'light');

      expect(tokens.colors.sectionHeader).toBeDefined();
    });
  });

  describe('dark theme contrast', () => {
    it('should provide sufficient contrast for dark theme', () => {
      const tokens = deriveSemanticTokens(TELEGRAM_DARK_THEME, 'dark');

      expect(tokens.colors.background.primary).toBe('#1c1c1d');
      expect(tokens.colors.text.primary).toBe('#ffffff');
      expect(tokens.colors.text.hint).toBe('#aaaaaa');

      const bgLuminance = 0.299 * 28 + 0.587 * 28 + 0.114 * 29;
      const textLuminance = 1.0;

      const contrastRatio = (textLuminance + 0.05) / (bgLuminance / 255 + 0.05);
      expect(contrastRatio).toBeGreaterThan(4.5);
    });
  });

  describe('light theme contrast', () => {
    it('should provide sufficient contrast for light theme', () => {
      const tokens = deriveSemanticTokens(TELEGRAM_LIGHT_THEME, 'light');

      expect(tokens.colors.background.primary).toBe('#ffffff');
      expect(tokens.colors.text.primary).toBe('#000000');

      const bgLuminance = 1.0;
      const textLuminance = 0.0;

      const contrastRatio = (bgLuminance + 0.05) / (textLuminance + 0.05);
      expect(contrastRatio).toBeGreaterThan(4.5);
    });
  });

  describe('link color', () => {
    it('should use Telegram blue for links in light theme', () => {
      const tokens = deriveSemanticTokens(TELEGRAM_LIGHT_THEME, 'light');

      expect(tokens.colors.text.link).toBe('#3390ec');
    });

    it('should use lighter blue for links in dark theme', () => {
      const tokens = deriveSemanticTokens(TELEGRAM_DARK_THEME, 'dark');

      expect(tokens.colors.text.link).toBe('#64b5ef');
    });
  });

  describe('destructive color', () => {
    it('should have red destructive color in light theme', () => {
      const tokens = deriveSemanticTokens(TELEGRAM_LIGHT_THEME, 'light');

      expect(tokens.colors.text.destructive).toBe('#e53935');
    });

    it('should have lighter red destructive color in dark theme', () => {
      const tokens = deriveSemanticTokens(TELEGRAM_DARK_THEME, 'dark');

      expect(tokens.colors.text.destructive).toBe('#ff6b6b');
    });
  });
});