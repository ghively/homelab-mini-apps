/**
 * Unsupported client banner
 * Displays warning when Telegram WebApp API is unavailable
 */

import { DesignSystemElement } from './base.js';
import { ClientDetector } from '../client/detector.js';

export class UnsupportedClientBanner extends DesignSystemElement {
  private clientDetector: ClientDetector;

  static get observedAttributes(): string[] {
    return ['show-in-partial', 'message'];
  }

  constructor() {
    super();
    this.clientDetector = new ClientDetector();
  }

  connectedCallback(): void {
    super.connectedCallback();
    this.render();
  }

  attributeChangedCallback(): void {
    this.render();
  }

  private render(): void {
    const capabilities = this.clientDetector.getCapabilities();
    const showInPartial = this.getAttribute('show-in-partial') === 'true';
    const customMessage = this.getAttribute('message');

    const shouldShow =
      capabilities.status === 'no-telegram-support' ||
      (showInPartial && capabilities.status === 'partial-telegram-support');

    if (!shouldShow) {
      this.innerHTML = '';
      this.style.display = 'none';
      return;
    }

    const message =
      customMessage ||
      'Running in browser fallback mode. Some Telegram features may be limited.';

    const versionInfo = capabilities.webAppVersion
      ? ` Telegram WebApp v${capabilities.webAppVersion}`
      : '';

    const platformInfo = capabilities.platform ? ` on ${capabilities.platform}` : '';

    this.innerHTML = `
      <div part="banner" style="
        padding: 12px 16px;
        background: var(--ds-bg-secondary, #f4f4f5);
        border-bottom: 1px solid var(--ds-text-hint, #70757933);
        color: var(--ds-text-primary, #000000);
        font-size: 14px;
        line-height: 1.4;
        display: flex;
        align-items: center;
        gap: 8px;
      ">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style="flex-shrink: 0;">
          <path
            d="M10 6V10M10 14H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <span part="message">${message}${versionInfo}${platformInfo}</span>
      </div>
    `;

    this.style.display = 'block';
    this.setAttribute('data-client-status', capabilities.status);
  }

  public getCapabilities() {
    return this.clientDetector.getCapabilities();
  }

  public isSupported(): boolean {
    return this.clientDetector.isSupported();
  }

  public requiresFallback(): boolean {
    return this.clientDetector.requiresFallback();
  }
}

if (!customElements.get('ds-unsupported-client-banner')) {
  customElements.define('ds-unsupported-client-banner', UnsupportedClientBanner);
}