/**
 * Test setup for vitest
 */

import { cleanup } from '@testing-library/dom';
import { afterEach, vi } from 'vitest';

afterEach(() => {
  cleanup();
});

global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}));