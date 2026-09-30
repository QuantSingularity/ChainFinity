// Manual mock for axios used by the test-suite.
//
// `create` is a PLAIN function (not jest.fn) that always returns the same
// singleton instance. The previous version used `create: jest.fn(() => mockAxios)`,
// but several suites call `jest.clearAllMocks()` in beforeEach, which wipes a
// jest.fn's implementation - after that, `axios.create()` returned undefined
// and every `axios.create().post/get` access threw. Keeping `create` as a
// plain function makes it survive clearAllMocks while the individual verb
// methods remain jest.fn()s whose call history can still be asserted.
const makeFn = () => jest.fn(() => Promise.resolve({ data: {} }));

const mockAxios = {
  get: makeFn(),
  post: makeFn(),
  put: makeFn(),
  delete: makeFn(),
  patch: makeFn(),
  request: makeFn(),
  head: makeFn(),
  options: makeFn(),
  interceptors: {
    request: { use: jest.fn(), eject: jest.fn() },
    response: { use: jest.fn(), eject: jest.fn() },
  },
  defaults: { headers: { common: {} } },
  isAxiosError: (_error) => false,
  CancelToken: {
    source: () => ({ token: {}, cancel: () => {} }),
  },
};

// Stable factory: always returns the singleton, even after clearAllMocks.
mockAxios.create = () => mockAxios;

export default mockAxios;
