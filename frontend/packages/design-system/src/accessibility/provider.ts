/**
 * Accessibility primitives for Mini Apps
 * Handles reduced-motion preference, focus management, and contrast requirements
 */

export type ReducedMotionState = 'reduced' | 'no-preference' | 'unknown';

export interface AccessibilityState {
  prefersReducedMotion: ReducedMotionState;
  supportsHighContrast: boolean;
  hasKeyboardFocus: boolean;
  focusVisible: boolean;
}

export class AccessibilityProvider {
  private prefersReducedMotion: ReducedMotionState;
  private supportsHighContrast: boolean;
  private focusVisible: boolean;
  private listeners: Set<(state: AccessibilityState) => void> = new Set();

  constructor() {
    this.prefersReducedMotion = this.detectReducedMotion();
    this.supportsHighContrast = this.detectHighContrast();
    this.focusVisible = false;

    this.setupListeners();
  }

  private detectReducedMotion(): ReducedMotionState {
    if (typeof window === 'undefined' || !window.matchMedia) {
      return 'unknown';
    }

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    return mediaQuery.matches ? 'reduced' : 'no-preference';
  }

  private detectHighContrast(): boolean {
    if (typeof window === 'undefined' || !window.matchMedia) {
      return false;
    }

    const mediaQuery = window.matchMedia('(prefers-contrast: more)');
    return mediaQuery.matches;
  }

  private setupListeners(): void {
    if (typeof window === 'undefined' || !window.matchMedia) {
      return;
    }

    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const handleMotionChange = (e: MediaQueryListEvent | MediaQueryList) => {
      this.prefersReducedMotion = e.matches ? 'reduced' : 'no-preference';
      this.notifyListeners();
    };

    reducedMotionQuery.addEventListener('change', handleMotionChange);

    window.addEventListener('keydown', this.handleKeyDown.bind(this));
    window.addEventListener('mousedown', this.handleMouseDown.bind(this));
  }

  private handleKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Tab') {
      this.focusVisible = true;
      this.notifyListeners();
    }
  }

  private handleMouseDown(): void {
    this.focusVisible = false;
    this.notifyListeners();
  }

  private notifyListeners(): void {
    const state: AccessibilityState = {
      prefersReducedMotion: this.prefersReducedMotion,
      supportsHighContrast: this.supportsHighContrast,
      hasKeyboardFocus: this.focusVisible,
      focusVisible: this.focusVisible
    };

    this.listeners.forEach((listener) => {
      try {
        listener(state);
      } catch (error) {
        console.error('Accessibility listener error:', error);
      }
    });
  }

  public getState(): AccessibilityState {
    return {
      prefersReducedMotion: this.prefersReducedMotion,
      supportsHighContrast: this.supportsHighContrast,
      hasKeyboardFocus: this.focusVisible,
      focusVisible: this.focusVisible
    };
  }

  public shouldReduceMotion(): boolean {
    return this.prefersReducedMotion === 'reduced';
  }

  public addListener(listener: (state: AccessibilityState) => void): () => void {
    this.listeners.add(listener);
    return () => this.removeListener(listener);
  }

  public removeListener(listener: (state: AccessibilityState) => void): void {
    this.listeners.delete(listener);
  }

  destroy(): void {
    this.listeners.clear();
  }
}