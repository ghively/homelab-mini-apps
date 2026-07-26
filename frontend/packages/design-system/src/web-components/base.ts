/**
 * Base custom element class with accessibility and lifecycle hooks
 */

export class DesignSystemElement extends HTMLElement {
  protected _connected = false;

  connectedCallback(): void {
    this._connected = true;
  }

  disconnectedCallback(): void {
    this._connected = false;
  }

  protected emit<T>(name: string, detail: T): void {
    const event = new CustomEvent<T>(name, {
      bubbles: true,
      composed: true,
      detail
    });
    this.dispatchEvent(event);
  }

  protected setAttributeIfChanged(name: string, value: string | null): void {
    const current = this.getAttribute(name);
    if (current !== value) {
      if (value === null) {
        this.removeAttribute(name);
      } else {
        this.setAttribute(name, value);
      }
    }
  }
}