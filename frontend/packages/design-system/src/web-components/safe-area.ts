/**
 * Safe area wrapper element
 * Applies content-safe-area and viewport-stable-height constraints
 */

import { DesignSystemElement } from './base.js';
import { SafeAreaProvider } from '../safe-area/provider.js';

export class SafeAreaWrapper extends DesignSystemElement {
  protected safeAreaProvider: SafeAreaProvider;

  static get observedAttributes(): string[] {
    return ['expand-on-mount'];
  }

  constructor() {
    super();
    this.safeAreaProvider = new SafeAreaProvider();
  }

  connectedCallback(): void {
    super.connectedCallback();
    this.applySafeArea();

    if (this.getAttribute('expand-on-mount') === 'true') {
      this.safeAreaProvider.expand();
    }
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this.safeAreaProvider.destroy();
  }

  attributeChangedCallback(name: string, oldValue: string | null, newValue: string | null): void {
    if (name === 'expand-on-mount' && oldValue !== newValue && newValue === 'true') {
      this.safeAreaProvider.expand();
    }
  }

  private applySafeArea(): void {
    const insets = this.safeAreaProvider.getSafeAreaInsets();
    const viewport = this.safeAreaProvider.getViewportData();
    const isTelegram = this.safeAreaProvider.isTelegramContext();

    this.style.setProperty('--ds-safe-area-top', `${insets.top}px`);
    this.style.setProperty('--ds-safe-area-right', `${insets.right}px`);
    this.style.setProperty('--ds-safe-area-bottom', `${insets.bottom}px`);
    this.style.setProperty('--ds-safe-area-left', `${insets.left}px`);

    this.style.setProperty('--ds-viewport-height', `${viewport.height}px`);
    this.style.setProperty('--ds-viewport-width', `${viewport.width}px`);
    this.style.setProperty('--ds-viewport-stable-height', `${viewport.stableHeight}px`);

    this.style.setProperty('--ds-content-safe-area-top', `${insets.top}px`);
    this.style.setProperty('--ds-content-safe-area-right', `${insets.right}px`);
    this.style.setProperty('--ds-content-safe-area-bottom', `${insets.bottom}px`);
    this.style.setProperty('--ds-content-safe-area-left', `${insets.left}px`);

    if (isTelegram) {
      this.setAttribute('data-telegram-context', 'true');
      this.setAttribute('data-viewport-expanded', String(viewport.isExpanded));
    } else {
      this.setAttribute('data-telegram-context', 'false');
    }
  }

  public expand(): void {
    this.safeAreaProvider.expand();
  }

  public getSafeAreaInsets() {
    return this.safeAreaProvider.getSafeAreaInsets();
  }

  public getViewportData() {
    return this.safeAreaProvider.getViewportData();
  }
}

if (!customElements.get('ds-safe-area')) {
  customElements.define('ds-safe-area', SafeAreaWrapper);
}