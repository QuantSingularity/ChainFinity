// jest-dom adds custom matchers like toBeInTheDocument()
import "@testing-library/jest-dom";

// ── window.matchMedia ─────────────────────────────────────────────────────────
// jsdom does not implement matchMedia. MUI's useMediaQuery reads `.matches`
// and framer-motion's reduced-motion detection reads `.addListener`, so both
// crash without this. It is defined with a plain function (not jest.fn) so it
// survives jest's automatic mock reset between tests - the previous
// jest.fn().mockImplementation lost its return value once mocks were reset,
// which made matchMedia() return undefined and broke ~27 tests.
Object.defineProperty(window, "matchMedia", {
  writable: true,
  configurable: true,
  value: (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {}, // deprecated
    removeListener: () => {}, // deprecated
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// ── ResizeObserver ────────────────────────────────────────────────────────────
// Recharts' ResponsiveContainer instantiates a ResizeObserver, which jsdom
// does not provide. Without this, every chart-bearing component throws
// "ResizeObserver is not defined".
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
global.ResizeObserver = ResizeObserverMock;
window.ResizeObserver = ResizeObserverMock;

// ── IntersectionObserver ──────────────────────────────────────────────────────
// Some framer-motion / lazy-render paths rely on it.
class IntersectionObserverMock {
  constructor() {
    this.root = null;
    this.rootMargin = "";
    this.thresholds = [];
  }
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() {
    return [];
  }
}
global.IntersectionObserver = IntersectionObserverMock;
window.IntersectionObserver = IntersectionObserverMock;

// ── localStorage ──────────────────────────────────────────────────────────────
// A functional in-memory implementation whose methods are ALSO jest spies, so
// tests can both rely on real storage behaviour (getItem returns what was set)
// and assert calls via toHaveBeenCalledWith. The previous all-jest.fn mock
// returned undefined from getItem (breaking the auth context), while a plain
// non-spy implementation broke tests that assert on setItem/removeItem.
const createLocalStorageMock = () => {
  let store = {};
  return {
    getItem: jest.fn((key) => (key in store ? store[key] : null)),
    setItem: jest.fn((key, value) => {
      store[key] = String(value);
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
    key: jest.fn((i) => Object.keys(store)[i] || null),
    get length() {
      return Object.keys(store).length;
    },
  };
};
Object.defineProperty(window, "localStorage", {
  writable: true,
  configurable: true,
  value: createLocalStorageMock(),
});

// Reset storage AND spy history between tests so nothing leaks across cases.
beforeEach(() => {
  window.localStorage.clear();
  window.localStorage.getItem.mockClear();
  window.localStorage.setItem.mockClear();
  window.localStorage.removeItem.mockClear();
  window.localStorage.clear.mockClear();
});

// ── scrollTo ──────────────────────────────────────────────────────────────────
window.scrollTo = () => {};
