import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { SafeAreaWrapper } from '../src/web-components/safe-area.js';

describe('SafeAreaWrapper web component', () => {
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
      expand: vi.fn(),
      onEvent: vi.fn(),
      offEvent: vi.fn()
    };

    (global as any).window = {
      innerHeight: 800,
      innerWidth: 400,
      Telegram: { WebApp: mockWebApp }
    };

    if (!customElements.get('ds-safe-area')) {
      customElements.define('ds-safe-area', SafeAreaWrapper);
    }
  });

  afterEach(() => {
    const element = document.querySelector('ds-safe-area');
    element?.remove();
    delete (global as any).window;
  });

  describe('initialization', () => {
    it('should apply safe area CSS variables', () => {
      const element = document.createElement('ds-safe-area');
      document.body.appendChild(element);

      expect(element.style.getPropertyValue('--ds-safe-area-top')).toBe('44px');
      expect(element.style.getPropertyValue('--ds-safe-area-bottom')).toBe('34px');
      expect(element.style.getPropertyValue('--ds-safe-area-left')).toBe('0px');
      expect(element.style.getPropertyValue('--ds-safe-area-right')).toBe('0px');
    });

    it('should apply viewport CSS variables', () => {
      const element = document.createElement('ds-safe-area');
      document.body.appendChild(element);

      expect(element.style.getPropertyValue('--ds-viewport-height')).toBe('800px');
      expect(element.style.getPropertyValue('--ds-viewport-width')).toBe('400px');
      expect(element.style.getPropertyValue('--ds-viewport-stable-height')).toBe('750px');
    });

    it('should apply content safe area CSS variables', () => {
      const element = document.createElement('ds-safe-area');
      document.body.appendChild(element);

      expect(element.style.getPropertyValue('--ds-content-safe-area-top')).toBe('44px');
      expect(element.style.getPropertyValue('--ds-content-safe-area-bottom')).toBe('34px');
    });

    it('should mark telegram context', () => {
      const element = document.createElement('ds-safe-area');
      document.body.appendChild(element);

      expect(element.getAttribute('data-telegram-context')).toBe('true');
      expect(element.getAttribute('data-viewport-expanded')).toBe('false');
    });
  });

  describe('expand on mount', () => {
    it('should expand when expand-on-mount is true', () => {
      const element = document.createElement('ds-safe-area');
      element.setAttribute('expand-on-mount', 'true');
      document.body.appendChild(element);

      expect(mockWebApp.expand).toHaveBeenCalled();
    });

    it('should not expand when expand-on-mount is false', () => {
      const element = document.createElement('ds-safe-area');
      element.setAttribute('expand-on-mount', 'false');
      document.body.appendChild(element);

      expect(mockWebApp.expand).not.toHaveBeenCalled();
    });

    it('should expand when attribute changes to true', () => {
      const element = document.createElement('ds-safe-area');
      document.body.appendChild(element);

      element.setAttribute('expand-on-mount', 'true');

      expect(mockWebApp.expand).toHaveBeenCalled();
    });
  });

  describe('viewport changes', () => {
    it('should update on viewport changed event', () => {
      const element = document.createElement('ds-safe-area');
      document.body.appendChild(element);

      mockWebApp.viewportHeight = 900;
      mockWebApp.viewportStableHeight = 850;
      mockWebApp.isExpanded = true;

      const callback = mockWebApp.onEvent.mock.calls.find((call: any[]) => call[0] === 'viewportChanged')?.[1];
      callback?.();

      expect(element.style.getPropertyValue('--ds-viewport-height')).toBe('900px');
      expect(element.style.getPropertyValue('--ds-viewport-stable-height')).toBe('850px');
      expect(element.getAttribute('data-viewport-expanded')).toBe('true');
    });
  });

  describe('fallback when no telegram', () => {
    beforeEach(() => {
      delete (global as any).window;
      (global as any).window = {
        innerHeight: 1000,
        innerWidth: 500
      };
    });

    it('should use window dimensions as fallback', () => {
      const element = document.createElement('ds-safe-area');
      document.body.appendChild(element);

      expect(element.style.getPropertyValue('--ds-safe-area-top')).toBe('0px');
      expect(element.style.getPropertyValue('--ds-viewport-height')).toBe('1000px');
      expect(element.style.getPropertyValue('--ds-viewport-width')).toBe('500px');
    });

    it('should mark no telegram context', () => {
      const element = document.createElement('ds-safe-area');
      document.body.appendChild(element);

      expect(element.getAttribute('data-telegram-context')).toBe('false');
    });

    it('should not call expand when no telegram', () => {
      const element = document.createElement('ds-safe-area');
      element.setAttribute('expand-on-mount', 'true');
      document.body.appendChild(element);

      expect(() => element.expand()).not.toThrow();
    });
  });

  describe('public API', () => {
    it('should expose getSafeAreaInsets', () => {
      const element = document.createElement('ds-safe-area');
      document.body.appendChild(element);

      const insets = element.getSafeAreaInsets();
      expect(insets.top).toBe(44);
      expect(insets.bottom).toBe(34);
    });

    it('should expose getViewportData', () => {
      const element = document.createElement('ds-safe-area');
      document.body.appendChild(element);

      const viewport = element.getViewportData();
      expect(viewport.height).toBe(800);
      expect(viewport.stableHeight).toBe(750);
    });

    it('should expose expand method', () => {
      const element = document.createElement('ds-safe-area');
      document.body.appendChild(element);

      element.expand();

      expect(mockWebApp.expand).toHaveBeenCalled();
    });
  });

  describe('cleanup', () => {
    it('should remove event listeners on disconnect', () => {
      const element = document.createElement('ds-safe-area');
      document.body.appendChild(element);

      element.remove();

      expect(mockWebApp.offEvent).toHaveBeenCalled();
    });
  });
});