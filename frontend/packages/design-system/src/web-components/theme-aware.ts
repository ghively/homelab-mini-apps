/**
 * Theme-aware custom element base class
 * Automatically applies Telegram theme tokens as CSS custom properties
 */

import { DesignSystemElement } from './base.js';
import { ThemeProvider } from '../theme/provider.js';
import type { SemanticTokens } from '../tokens/semantic.js';

export class ThemeAwareElement extends DesignSystemElement {
  protected themeProvider: ThemeProvider;
  private themeChangeUnsubscribe: (() => void) | null = null;

  constructor() {
    super();
    this.themeProvider = new ThemeProvider();
  }

  connectedCallback(): void {
    super.connectedCallback();
    this.applyTheme(this.themeProvider.getCurrentTheme());

    this.themeChangeUnsubscribe = this.themeProvider.addListener((event) => {
      this.applyTheme(this.themeProvider.getCurrentTheme());
      this.emit('themechange', event);
    });
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this.themeChangeUnsubscribe?.();
    this.themeProvider.destroy();
  }

  protected applyTheme(theme: SemanticTokens): void {
    const { colors, colorScheme } = theme;

    this.style.setProperty('--ds-color-scheme', colorScheme);

    this.style.setProperty('--ds-bg-primary', colors.background.primary);
    this.style.setProperty('--ds-bg-secondary', colors.background.secondary);
    this.style.setProperty('--ds-bg-header', colors.background.header);
    this.style.setProperty('--ds-bg-section', colors.background.section);

    this.style.setProperty('--ds-text-primary', colors.text.primary);
    this.style.setProperty('--ds-text-secondary', colors.text.secondary);
    this.style.setProperty('--ds-text-hint', colors.text.hint);
    this.style.setProperty('--ds-text-link', colors.text.link);
    this.style.setProperty('--ds-text-destructive', colors.text.destructive);

    this.style.setProperty('--ds-button-bg', colors.button.background);
    this.style.setProperty('--ds-button-text', colors.button.text);

    this.style.setProperty('--ds-section-header', colors.sectionHeader);

    this.setAttribute('data-color-scheme', colorScheme);
  }

  protected getCurrentTheme(): SemanticTokens {
    return this.themeProvider.getCurrentTheme();
  }
}