import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ClientDetector } from '../src/client/detector.js';

describe('ClientDetector', () => {
  let mockWebApp: any;

  beforeEach(() => {
    mockWebApp = {
      version: '6.9',
      platform: 'ios',
      themeParams: {
        bg_color: '#ffffff',
        text_color: '#000000'
      },
      colorScheme: 'light',
      safeAreaInsets: { top: 44, right: 0, bottom: 34, left: 0 },
      viewportHeight: 800,
      HapticFeedback: {},
      enableClosingConfirmation: vi.fn()
    };

    (global as any).window = {
      Telegram: { WebApp: mockWebApp }
    };
  });

  afterEach(() => {
    delete (global as any).window;
  });

  describe('full telegram support', () => {
    it('should detect full Telegram support', () => {
      const detector = new ClientDetector();
      const capabilities = detector.getCapabilities();

      expect(capabilities.status).toBe('full-telegram-support');
      expect(capabilities.hasThemeSupport).toBe(true);
      expect(capabilities.hasSafeAreaSupport).toBe(true);
      expect(capabilities.hasViewportSupport).toBe(true);
      expect(capabilities.hasHapticFeedback).toBe(true);
      expect(capabilities.hasClosingConfirmation).toBe(true);
    });

    it('should be supported', () => {
      const detector = new ClientDetector();
      expect(detector.isSupported()).toBe(true);
    });

    it('should not require fallback', () => {
      const detector = new ClientDetector();
      expect(detector.requiresFallback()).toBe(false);
    });
  });

  describe('partial support', () => {
    it('should detect partial Telegram support', () => {
      delete mockWebApp.HapticFeedback;
      delete mockWebApp.enableClosingConfirmation;

      const detector = new ClientDetector();
      const capabilities = detector.getCapabilities();

      expect(capabilities.status).toBe('partial-telegram-support');
      expect(capabilities.hasThemeSupport).toBe(true);
      expect(capabilities.hasViewportSupport).toBe(true);
      expect(capabilities.hasHapticFeedback).toBe(false);
    });

    it('should be supported with partial support', () => {
      delete mockWebApp.HapticFeedback;
      const detector = new ClientDetector();

      expect(detector.isSupported()).toBe(true);
    });
  });

  describe('no telegram support', () => {
    it('should detect no Telegram support', () => {
      delete (global as any).window;

      const detector = new ClientDetector();
      const capabilities = detector.getCapabilities();

      expect(capabilities.status).toBe('no-telegram-support');
      expect(capabilities.hasThemeSupport).toBe(false);
      expect(capabilities.hasSafeAreaSupport).toBe(false);
      expect(capabilities.hasViewportSupport).toBe(false);
      expect(capabilities.webAppVersion).toBe(null);
      expect(capabilities.platform).toBe(null);
    });

    it('should not be supported', () => {
      delete (global as any).window;
      const detector = new ClientDetector();

      expect(detector.isSupported()).toBe(false);
    });

    it('should require fallback', () => {
      delete (global as any).window;
      const detector = new ClientDetector();

      expect(detector.requiresFallback()).toBe(true);
    });

    it('should provide fallback reason', () => {
      delete (global as any).window;
      const detector = new ClientDetector();

      expect(detector.getFallbackReason()).toContain('Telegram WebApp API is not available');
    });
  });

  describe('version checking', () => {
    it('should return version', () => {
      const detector = new ClientDetector();
      expect(detector.getVersion()).toBe('6.9');
    });

    it('should return platform', () => {
      const detector = new ClientDetector();
      expect(detector.getPlatform()).toBe('ios');
    });

    it('should check minimum version correctly', () => {
      const detector = new ClientDetector();

      expect(detector.hasMinimumVersion('6.0')).toBe(true);
      expect(detector.hasMinimumVersion('6.9')).toBe(true);
      expect(detector.hasMinimumVersion('7.0')).toBe(false);
    });

    it('should handle version comparisons with different lengths', () => {
      const detector = new ClientDetector();

      expect(detector.hasMinimumVersion('6')).toBe(true);
      expect(detector.hasMinimumVersion('6.8')).toBe(true);
    });

    it('should return false for version check when no version', () => {
      delete mockWebApp.version;
      const detector = new ClientDetector();

      expect(detector.hasMinimumVersion('6.0')).toBe(false);
    });
  });

  describe('missing theme params', () => {
    it('should detect missing theme support', () => {
      delete mockWebApp.themeParams;

      const detector = new ClientDetector();
      const capabilities = detector.getCapabilities();

      expect(capabilities.hasThemeSupport).toBe(false);
    });
  });

  describe('missing safe area', () => {
    it('should detect missing safe area support', () => {
      delete mockWebApp.safeAreaInsets;

      const detector = new ClientDetector();
      const capabilities = detector.getCapabilities();

      expect(capabilities.hasSafeAreaSupport).toBe(false);
    });
  });
});