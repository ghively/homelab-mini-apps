import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { UnsupportedClientBanner } from '../src/web-components/unsupported-client.js';

describe('UnsupportedClientBanner', () => {
  beforeEach(() => {
    customElements.define('ds-unsupported-client-banner', UnsupportedClientBanner);
  });

  afterEach(() => {
    const element = document.querySelector('ds-unsupported-client-banner');
    element?.remove();
  });

  describe('no telegram support', () => {
    beforeEach(() => {
      delete (global as any).window;
    });

    it('should display banner when no Telegram support', () => {
      const element = document.createElement('ds-unsupported-client-banner');
      document.body.appendChild(element);

      expect(element.style.display).toBe('block');
      expect(element.getAttribute('data-client-status')).toBe('no-telegram-support');
    });

    it('should show default message', () => {
      const element = document.createElement('ds-unsupported-client-banner');
      document.body.appendChild(element);

      const messagePart = element.querySelector('[part="message"]');
      expect(messagePart?.textContent).toContain('browser fallback mode');
    });

    it('should require fallback', () => {
      const element = document.createElement('ds-unsupported-client-banner');
      document.body.appendChild(element);

      expect(element.requiresFallback()).toBe(true);
    });

    it('should not be supported', () => {
      const element = document.createElement('ds-unsupported-client-banner');
      document.body.appendChild(element);

      expect(element.isSupported()).toBe(false);
    });

    it('should allow custom message', () => {
      const element = document.createElement('ds-unsupported-client-banner');
      element.setAttribute('message', 'Custom warning message');
      document.body.appendChild(element);

      const messagePart = element.querySelector('[part="message"]');
      expect(messagePart?.textContent).toContain('Custom warning message');
    });
  });

  describe('partial telegram support', () => {
    beforeEach(() => {
      (global as any).window = {
        Telegram: {
          WebApp: {
            version: '6.0',
            platform: 'android',
            themeParams: { bg_color: '#ffffff' }
          }
        }
      };
    });

    it('should hide banner by default for partial support', () => {
      const element = document.createElement('ds-unsupported-client-banner');
      document.body.appendChild(element);

      expect(element.style.display).toBe('none');
    });

    it('should show banner when show-in-partial is true', () => {
      const element = document.createElement('ds-unsupported-client-banner');
      element.setAttribute('show-in-partial', 'true');
      document.body.appendChild(element);

      expect(element.style.display).toBe('block');
      expect(element.getAttribute('data-client-status')).toBe('partial-telegram-support');
    });

    it('should be supported with partial support', () => {
      const element = document.createElement('ds-unsupported-client-banner');
      document.body.appendChild(element);

      expect(element.isSupported()).toBe(true);
    });

    it('should not require fallback with partial support', () => {
      const element = document.createElement('ds-unsupported-client-banner');
      document.body.appendChild(element);

      expect(element.requiresFallback()).toBe(false);
    });
  });

  describe('full telegram support', () => {
    beforeEach(() => {
      (global as any).window = {
        Telegram: {
          WebApp: {
            version: '6.9',
            platform: 'ios',
            themeParams: { bg_color: '#ffffff', text_color: '#000000' },
            colorScheme: 'light',
            safeAreaInsets: { top: 44 },
            viewportHeight: 800,
            HapticFeedback: {},
            enableClosingConfirmation: () => {}
          }
        }
      };
    });

    it('should hide banner when full support', () => {
      const element = document.createElement('ds-unsupported-client-banner');
      document.body.appendChild(element);

      expect(element.style.display).toBe('none');
    });

    it('should stay hidden with show-in-partial', () => {
      const element = document.createElement('ds-unsupported-client-banner');
      element.setAttribute('show-in-partial', 'true');
      document.body.appendChild(element);

      expect(element.style.display).toBe('none');
    });

    it('should report full support', () => {
      const element = document.createElement('ds-unsupported-client-banner');
      document.body.appendChild(element);

      expect(element.isSupported()).toBe(true);
      expect(element.requiresFallback()).toBe(false);
    });
  });

  describe('capabilities', () => {
    it('should expose client capabilities', () => {
      delete (global as any).window;

      const element = document.createElement('ds-unsupported-client-banner');
      document.body.appendChild(element);

      const capabilities = element.getCapabilities();
      expect(capabilities.status).toBe('no-telegram-support');
    });
  });
});