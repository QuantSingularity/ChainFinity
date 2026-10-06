import axios from "axios";
import {
  aiAPI,
  authAPI,
  blockchainAPI,
  handleApiError,
  portfolioAPI,
  riskAPI,
} from "../services/api";

jest.mock("axios");

describe("API Services", () => {
  describe("handleApiError", () => {
    test("handles response errors correctly", () => {
      const error = {
        response: {
          status: 404,
          data: { detail: "Not found" },
        },
      };

      const result = handleApiError(error);
      expect(result).toEqual({
        status: 404,
        message: "Not found",
      });
    });

    test("handles request errors correctly", () => {
      const error = {
        request: {},
      };

      const result = handleApiError(error);
      expect(result).toEqual({
        status: 0,
        message: "No response from server. Please check your connection.",
      });
    });

    test("handles unknown errors correctly", () => {
      const error = {
        message: "Unknown error",
      };

      const result = handleApiError(error);
      expect(result).toEqual({
        status: 0,
        message: "Unknown error",
      });
    });
  });

  describe("authAPI", () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    test("register calls correct endpoint", async () => {
      const mockData = { id: 1, email: "test@example.com" };
      const mockResponse = { data: mockData };
      axios.create().post.mockResolvedValue(mockResponse);

      const userData = {
        name: "Test User",
        email: "test@example.com",
        password: "password123",
      };

      const result = await authAPI.register(userData);
      expect(result.data).toEqual(mockData);
    });

    test("login calls correct endpoint", async () => {
      const mockData = { access_token: "token123", token_type: "Bearer" };
      const mockResponse = { data: mockData };
      axios.create().post.mockResolvedValue(mockResponse);

      const credentials = {
        email: "test@example.com",
        password: "password123",
      };

      const result = await authAPI.login(credentials);
      expect(result.data).toEqual(mockData);
    });
  });

  describe("blockchainAPI", () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    test("getPortfolio calls correct endpoint", async () => {
      const mockData = {
        total_value: "10000.00",
        assets: [{ symbol: "ETH", balance: "5" }],
      };
      const mockResponse = { data: mockData };
      axios.create().get.mockResolvedValue(mockResponse);

      const walletAddress = "0x1234567890abcdef";
      const result = await blockchainAPI.getPortfolio(walletAddress);
      expect(result.data).toEqual(mockData);
    });

    test("getTransactions calls correct endpoint", async () => {
      const mockData = [
        { id: 1, type: "send", amount: "1 ETH" },
        { id: 2, type: "receive", amount: "2 ETH" },
      ];
      const mockResponse = { data: mockData };
      axios.create().get.mockResolvedValue(mockResponse);

      const walletAddress = "0x1234567890abcdef";
      const result = await blockchainAPI.getTransactions(walletAddress);
      expect(result.data).toEqual(mockData);
    });
  });

  describe("risk and ai APIs", () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    test("portfolioAPI.list paginates", async () => {
      await portfolioAPI.list(2, 10);
      expect(axios.create().get).toHaveBeenCalledWith("/api/v1/portfolios/", {
        params: { page: 2, size: 10 },
      });
    });

    test("riskAPI.assess posts to the assessment endpoint", async () => {
      await riskAPI.assess("abc");
      expect(axios.create().post).toHaveBeenCalledWith(
        "/api/v1/risk/assess/abc",
      );
    });

    test("riskAPI.stressTest passes the scenario", async () => {
      await riskAPI.stressTest("abc", "Crypto Winter");
      expect(axios.create().post).toHaveBeenCalledWith(
        "/api/v1/risk/stress-test/abc",
        null,
        { params: { scenario: "Crypto Winter" } },
      );
    });

    test("aiAPI.getPortfolioInsights passes the horizon", async () => {
      await aiAPI.getPortfolioInsights("abc", 14);
      expect(axios.create().get).toHaveBeenCalledWith(
        "/api/v1/ai/portfolio/abc/insights",
        { params: { horizon_days: 14 } },
      );
    });

    test("aiAPI posts model payloads", async () => {
      await aiAPI.forecastVolatility({ symbol: "BTC" });
      expect(axios.create().post).toHaveBeenCalledWith(
        "/api/v1/ai/volatility",
        {
          symbol: "BTC",
        },
      );
      await aiAPI.getStatus();
      expect(axios.create().get).toHaveBeenCalledWith("/api/v1/ai/status");
    });
  });
});
