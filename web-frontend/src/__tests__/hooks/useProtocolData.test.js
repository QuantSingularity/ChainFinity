import { act, renderHook, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";

jest.mock("../context/AppContext", () => ({
  useApp: () => ({
    user: { wallet_address: "0xUSER_WALLET" },
  }),
}));

jest.mock("../services/api", () => ({
  blockchainAPI: {
    getPortfolio: jest.fn(),
    getTransactions: jest.fn(),
    getTokenBalance: jest.fn(),
    getEthBalance: jest.fn(),
  },
  handleApiError: jest.fn((err) => ({
    status: 0,
    message: err?.message || "Error",
  })),
}));

const { blockchainAPI } = require("../services/api");
const {
  usePortfolioData,
  useTransactionHistory,
  useTokenBalance,
  useEthBalance,
} = require("../hooks/useProtocolData");

describe("useProtocolData hooks", () => {
  beforeEach(() => jest.clearAllMocks());

  describe("usePortfolioData", () => {
    test("fetches portfolio with provided walletAddress", async () => {
      const mockData = { total_value: "5000", assets: [] };
      blockchainAPI.getPortfolio.mockResolvedValue({ data: mockData });

      const { result } = renderHook(() =>
        usePortfolioData("0xPROVIDED_WALLET")
      );

      await waitFor(() => expect(result.current.loading).toBe(false));
      expect(result.current.portfolioData).toEqual(mockData);
      expect(blockchainAPI.getPortfolio).toHaveBeenCalledWith(
        "0xPROVIDED_WALLET"
      );
    });

    test("falls back to user wallet_address when none provided", async () => {
      const mockData = { total_value: "1000", assets: [] };
      blockchainAPI.getPortfolio.mockResolvedValue({ data: mockData });

      const { result } = renderHook(() => usePortfolioData(null));

      await waitFor(() => expect(result.current.loading).toBe(false));
      expect(blockchainAPI.getPortfolio).toHaveBeenCalledWith("0xUSER_WALLET");
    });

    test("sets error on API failure", async () => {
      blockchainAPI.getPortfolio.mockRejectedValue(new Error("Network error"));

      const { result } = renderHook(() =>
        usePortfolioData("0xPROVIDED_WALLET")
      );

      await waitFor(() => expect(result.current.loading).toBe(false));
      expect(result.current.error).not.toBeNull();
    });

    test("sets loading false immediately with no address", async () => {
      jest.mock("../context/AppContext", () => ({
        useApp: () => ({ user: null }),
      }));
      blockchainAPI.getPortfolio.mockResolvedValue({ data: {} });

      const { result } = renderHook(() => usePortfolioData(null));
      await waitFor(() => expect(result.current.loading).toBe(false));
    });
  });

  describe("useTransactionHistory", () => {
    test("fetches transactions with provided walletAddress", async () => {
      const mockTxs = [{ id: 1, type: "send" }];
      blockchainAPI.getTransactions.mockResolvedValue({ data: mockTxs });

      const { result } = renderHook(() =>
        useTransactionHistory("0xWALLET")
      );

      await waitFor(() => expect(result.current.loading).toBe(false));
      expect(result.current.transactions).toEqual(mockTxs);
    });

    test("sets error on failure", async () => {
      blockchainAPI.getTransactions.mockRejectedValue(new Error("Fail"));
      const { result } = renderHook(() => useTransactionHistory("0xWALLET"));
      await waitFor(() => expect(result.current.loading).toBe(false));
      expect(result.current.error).not.toBeNull();
    });
  });

  describe("useTokenBalance", () => {
    test("fetches token balance", async () => {
      blockchainAPI.getTokenBalance.mockResolvedValue({
        data: { balance: "100" },
      });

      const { result } = renderHook(() =>
        useTokenBalance("0xTOKEN", "ethereum")
      );

      await waitFor(() => expect(result.current.loading).toBe(false));
      expect(result.current.balance).toEqual({ balance: "100" });
    });

    test("does nothing with no tokenAddress", async () => {
      const { result } = renderHook(() => useTokenBalance(null));
      await waitFor(() => expect(result.current.loading).toBe(false));
      expect(blockchainAPI.getTokenBalance).not.toHaveBeenCalled();
    });
  });

  describe("useEthBalance", () => {
    test("fetches ETH balance", async () => {
      blockchainAPI.getEthBalance.mockResolvedValue({
        data: { balance: "2.5" },
      });

      const { result } = renderHook(() => useEthBalance());

      await waitFor(() => expect(result.current.loading).toBe(false));
      expect(result.current.ethBalance).toBe("2.5");
    });

    test("sets error on failure", async () => {
      blockchainAPI.getEthBalance.mockRejectedValue(new Error("fail"));
      const { result } = renderHook(() => useEthBalance());
      await waitFor(() => expect(result.current.loading).toBe(false));
      expect(result.current.error).not.toBeNull();
    });
  });
});
