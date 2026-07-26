/**
 * Focus management for accessible keyboard navigation
 */

import { DesignSystemElement } from './base.js';
import { AccessibilityProvider } from '../accessibility/provider.js';

export class FocusTrap extends DesignSystemElement {
  private accessibilityProvider: AccessibilityProvider;
  private focusableElements: HTMLElement[] = [];
  private firstFocusable: HTMLElement | null = null;
  private lastFocusable: HTMLElement | null = null;
  private previouslyFocused: HTMLElement | null = null;

  static get observedAttributes(): string[] {
    return ['disabled', 'autofocus'];
  }

  constructor() {
    super();
    this.accessibilityProvider = new AccessibilityProvider();
  }

  connectedCallback(): void {
    super.connectedCallback();

    if (this.getAttribute('autofocus') === 'true') {
      this.previouslyFocused = document.activeElement as HTMLElement;
      setTimeout(() => this.focusFirst(), 0);
    }
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    if (this.previouslyFocused && this.contains(this.previouslyFocused)) {
      this.previouslyFocused.focus();
    }
    this.accessibilityProvider.destroy();
  }

  attributeChangedCallback(name: string): void {
    if (name === 'disabled') {
      this.updateFocusManagement();
    }
  }

  private updateFocusManagement(): void {
    if (this.getAttribute('disabled') === 'true') {
      this.removeEventListener('keydown', this.handleKeyDown);
    } else {
      this.addEventListener('keydown', this.handleKeyDown);
    }
  }

  private getFocusableElements(): HTMLElement[] {
    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'textarea:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]'
    ].join(', ');

    return Array.from(this.querySelectorAll(focusableSelectors)).filter(
      (el): el is HTMLElement => {
        const computed = window.getComputedStyle(el);
        return computed.display !== 'none' && computed.visibility !== 'hidden';
      }
    );
  }

  private handleKeyDown = (event: KeyboardEvent): void => {
    if (event.key !== 'Tab') return;

    this.focusableElements = this.getFocusableElements();

    if (this.focusableElements.length === 0) {
      event.preventDefault();
      return;
    }

    this.firstFocusable = this.focusableElements[0];
    this.lastFocusable = this.focusableElements[this.focusableElements.length - 1];

    if (event.shiftKey) {
      if (document.activeElement === this.firstFocusable) {
        event.preventDefault();
        this.lastFocusable?.focus();
      }
    } else {
      if (document.activeElement === this.lastFocusable) {
        event.preventDefault();
        this.firstFocusable?.focus();
      }
    }
  };

  public focusFirst(): void {
    this.focusableElements = this.getFocusableElements();
    if (this.focusableElements.length > 0) {
      this.focusableElements[0].focus();
    }
  }

  public focusLast(): void {
    this.focusableElements = this.getFocusableElements();
    if (this.focusableElements.length > 0) {
      this.focusableElements[this.focusableElements.length - 1].focus();
    }
  }

  public getAccessibilityState() {
    return this.accessibilityProvider.getState();
  }

  public shouldReduceMotion(): boolean {
    return this.accessibilityProvider.shouldReduceMotion();
  }
}

if (!customElements.get('ds-focus-trap')) {
  customElements.define('ds-focus-trap', FocusTrap);
}