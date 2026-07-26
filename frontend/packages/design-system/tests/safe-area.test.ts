import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { SafeAreaProvider } from '../src/safe-area/provider.js';

describe('SafeAreaProvider', () => {
  let mockWebApp: any;

  beforeEach(() => {
    mockWebApp = {
      viewportHeight: 800,
      viewportWidth: 400,
      viewportStableHeight: 750,
      isExpanded: false,
      safeAreaInsets: {
        top: 44,
        right: 0,
        bottom: 34,
        left: 0
      },
      onEvent: vi.fn(),
      offEvent: vi.fn()
    };

    (global as any).window = {
      innerHeight: 800,
      innerWidth: 400,
      Telegram: { WebApp: mockWebApp }
    };
  });

  afterEach(() => {
    delete (global as any).window;
  });

  describe('initialization', () => {
    it('should initialize with Telegram safe area insets', () => {
      const provider = new SafeAreaProvider();
      const insets = provider.getSafeAreaInsets();

      expect(insets.top).toBe(44);
      expect(insets.bottom).toBe(34);
      expect(insets.left).toBe(0);
      expect(insets.right).toBe(0);
    });

    it('should use fallback values when WebApp unavailable', () => {
      delete (global as any).window;
      const provider = new SafeAreaProvider();
      const insets = provider.getSafeAreaInsets();

      expect(insets.top).toBe(0);
      expect(insets.bottom).toBe(0);
      expect(insets.left).toBe(0);
      expect(insets.right).toBe(0);
    });

    it('should detect Telegram context', () => {
      const provider = new SafeAreaProvider();
      expect(provider.isTelegramContext()).toBe(true);
    });

    it('should report no Telegram context when unavailable', () => {
      delete (global as any).window;
      const provider = new SafeAreaProvider();
      expect(provider.isTelegramContext()).toBe(false);
    });
  });

  describe('viewport data', () => {
    it('should return viewport data from WebApp', () => {
      const provider = new SafeAreaProvider();
      const viewport = provider.getViewportData();

      expect(viewport.height).toBe(800);
      expect(viewport.width).toBe(400);
      expect(viewport.stableHeight).toBe(750);
      expect(viewport.isExpanded).toBe(false);
      expect(viewport.safeAreaInsets.top).toBe(44);
    });

    it('should use window dimensions as fallback', () => {
      delete (global as any).window;
      (global as any).window = {
        innerHeight: 1000,
        innerWidth: 500
      };

      const provider = new SafeAreaProvider();
      const viewport = provider.getViewportData();

      expect(viewport.height).toBe(1000);
      expect(viewport.width).toBe(500);
      expect(viewport.stableHeight).toBe(1000);
      expect(viewport.isExpanded).toBe(false);
    });

    it('should return stable height', () => {
      const provider = new SafeAreaProvider();
      expect(provider.getStableHeight()).toBe(750);
    });
  });

  describe('content safe area', () => {
    it('should return content safe area', () => {
      const provider = new SafeAreaProvider();
      const contentSafeArea = provider.getContentSafeArea();

      expect(contentSafeArea.top).toBe(44);
      expect(contentSafeArea.bottom).toBe(34);
      expect(contentSafeArea.left).toBe(0);
      expect(contentSafeArea.right).toBe(0);
    });
  });

  describe('viewport changes', () => {
    it('should update viewport data on change event', () => {
      const provider = new SafeAreaProvider();

      mockWebApp.viewportHeight = 900;
      mockWebApp.viewportStableHeight = 850;
      mockWebApp.isExpanded = true;

      const viewportChangeCallback = mockWebApp.onEvent.mock.calls.find(
        (call: any[]) => call[0] === 'viewportChanged'
      )?.[1];

      if (viewportChangeCallback) {
        viewportChangeCallback();
      }

      const viewport = provider.getViewportData();
      expect(viewport.height).toBe(900);
      expect(viewport.stableHeight).toBe(850);
      expect(viewport.isExpanded).toBe(true);
    });
  });

  describe('expand functionality', () => {
    it('should call expand on WebApp', () => {
      const provider = new SafeAreaProvider();

      mockWebApp.expand = vi.fn();
      provider.expand();

      expect(mockWebApp.expand).toHaveBeenCalled();
    });

    it('should not error when WebApp unavailable', () => {
      delete (global as any).window;
      const provider = new SafeAreaProvider();

      expect(() => provider.expand()).not.toThrow();
    });
  });

  describe('cleanup', () => {
    it('should remove event listeners on destroy', () => {
      const provider = new SafeAreaProvider();
      provider.destroy();

      expect(mockWebApp.offEvent).toHaveBeenCalled();
    });
  });
});