import "@testing-library/jest-dom";

declare global {
  namespace jest {
    interface Mock<T = any, Y extends any[] = any> {
      mockResolvedValueOnce(value: T): Mock<T, Y>;
      mockRejectedValueOnce(value: any): Mock<T, Y>;
    }
  }

  interface Window {
    navigator: Navigator & {
      credentials?: {
        get: () => Promise<any>;
      };
    };
  }
}
