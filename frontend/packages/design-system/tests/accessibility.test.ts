import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { AccessibilityProvider } from '../src/accessibility/provider.js';

describe('AccessibilityProvider', () => {
  let mockMatchMedia: any;

  beforeEach(() => {
    mockMatchMedia = vi.fn();

    (global as any).window = {
      matchMedia: mockMatchMedia,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn()
    };
  });

  afterEach(() => {
    delete (global as any).window;
  });

  describe('initialization', () => {
    it('should detect reduced motion preference', () => {
      mockMatchMedia.mockReturnValue({
        matches: true,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn()
      });

      const provider = new AccessibilityProvider();
      const state = provider.getState();

      expect(state.prefersReducedMotion).toBe('reduced');
    });

    it('should detect no preference for motion', () => {
      mockMatchMedia.mockReturnValue({
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn()
      });

      const provider = new AccessibilityProvider();
      const state = provider.getState();

      expect(state.prefersReducedMotion).toBe('no-preference');
    });

    it('should detect high contrast support', () => {
      mockMatchMedia.mockImplementation((query: string) => {
        if (query.includes('reduced-motion')) {
          return {
            matches: false,
            addEventListener: vi.fn(),
            removeEventListener: vi.fn()
          };
        }
        if (query.includes('prefers-contrast')) {
          return {
            matches: true,
            addEventListener: vi.fn(),
            removeEventListener: vi.fn()
          };
        }
        return { matches: false };
      });

      const provider = new AccessibilityProvider();
      const state = provider.getState();

      expect(state.supportsHighContrast).toBe(true);
    });

    it('should return unknown when matchMedia unavailable', () => {
      delete (global as any).window;
      const provider = new AccessibilityProvider();
      const state = provider.getState();

      expect(state.prefersReducedMotion).toBe('unknown');
      expect(state.supportsHighContrast).toBe(false);
    });
  });

  describe('focus management', () => {
    it('should detect keyboard focus on Tab key', () => {
      mockMatchMedia.mockReturnValue({
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn()
      });

      const provider = new AccessibilityProvider();

      const tabKeyEvent = new KeyboardEvent('keydown', { key: 'Tab' });
      (window as any).dispatchEvent(tabKeyEvent);

      const state = provider.getState();
      expect(state.hasKeyboardFocus).toBe(true);
      expect(state.focusVisible).toBe(true);
    });

    it('should clear focus visibility on mouse down', () => {
      mockMatchMedia.mockReturnValue({
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn()
      });

      const provider = new AccessibilityProvider();

      const tabKeyEvent = new KeyboardEvent('keydown', { key: 'Tab' });
      (window as any).dispatchEvent(tabKeyEvent);

      const mouseEvent = new MouseEvent('mousedown');
      (window as any).dispatchEvent(mouseEvent);

      const state = provider.getState();
      expect(state.focusVisible).toBe(false);
    });
  });

  describe('shouldReduceMotion helper', () => {
    it('should return true when reduced motion', () => {
      mockMatchMedia.mockReturnValue({
        matches: true,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn()
      });

      const provider = new AccessibilityProvider();
      expect(provider.shouldReduceMotion()).toBe(true);
    });

    it('should return false when no reduced motion', () => {
      mockMatchMedia.mockReturnValue({
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn()
      });

      const provider = new AccessibilityProvider();
      expect(provider.shouldReduceMotion()).toBe(false);
    });
  });

  describe('listeners', () => {
    it('should notify listeners on state change', () => {
      mockMatchMedia.mockReturnValue({
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn()
      });

      const provider = new AccessibilityProvider();
      const listener = vi.fn();
      provider.addListener(listener);

      const tabKeyEvent = new KeyboardEvent('keydown', { key: 'Tab' });
      (window as any).dispatchEvent(tabKeyEvent);

      expect(listener).toHaveBeenCalled();
      expect(listener.mock.calls[0][0].focusVisible).toBe(true);
    });

    it('should unsubscribe listener correctly', () => {
      mockMatchMedia.mockReturnValue({
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn()
      });

      const provider = new AccessibilityProvider();
      const listener = vi.fn();
      const unsubscribe = provider.addListener(listener);

      unsubscribe();

      const tabKeyEvent = new KeyboardEvent('keydown', { key: 'Tab' });
      (window as any).dispatchEvent(tabKeyEvent);

      expect(listener).not.toHaveBeenCalled();
    });

    it('should handle listener errors gracefully', () => {
      mockMatchMedia.mockReturnValue({
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn()
      });

      const provider = new AccessibilityProvider();
      const listener = vi.fn(() => {
        throw new Error('Listener error');
      });
      provider.addListener(listener);

      const tabKeyEvent = new KeyboardEvent('keydown', { key: 'Tab' });

      expect(() => (window as any).dispatchEvent(tabKeyEvent)).not.toThrow();
    });
  });

  describe('cleanup', () => {
    it('should clear listeners on destroy', () => {
      mockMatchMedia.mockReturnValue({
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn()
      });

      const provider = new AccessibilityProvider();
      const listener = vi.fn();
      provider.addListener(listener);

      provider.destroy();

      const tabKeyEvent = new KeyboardEvent('keydown', { key: 'Tab' });
      (window as any).dispatchEvent(tabKeyEvent);

      expect(listener).not.toHaveBeenCalled();
    });
  });
});