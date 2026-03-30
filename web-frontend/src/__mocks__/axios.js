const mockAxios = {
  create: jest.fn(() => mockAxios),
  get: jest.fn(() => Promise.resolve({ data: {} })),
  post: jest.fn(() => Promise.resolve({ data: {} })),
  put: jest.fn(() => Promise.resolve({ data: {} })),
  delete: jest.fn(() => Promise.resolve({ data: {} })),
  patch: jest.fn(() => Promise.resolve({ data: {} })),
  request: jest.fn(() => Promise.resolve({ data: {} })),
  head: jest.fn(() => Promise.resolve({ data: {} })),
  options: jest.fn(() => Promise.resolve({ data: {} })),
  interceptors: {
    request: { use: jest.fn(), eject: jest.fn() },
    response: { use: jest.fn(), eject: jest.fn() },
  },
  defaults: { headers: {} },
  isAxiosError: jest.fn((_error) => false),
  CancelToken: {
    source: jest.fn(() => ({ token: {}, cancel: jest.fn() })),
    isCancel: jest.fn((_value) => false),
  },
};

export default mockAxios;
