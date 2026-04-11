import { renderHook, act, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import React from "react";
import { AppProvider } from "@/context/AppContext";
import {
  useTransactionHistory,
  usePortfolioData,
  useEthBalance,
} from "@/hooks/useProtocolData";
import * as apiModule from "@/services/api";

jest.mock("@/services/api");

const wrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(AppProvider, null, children);

describe("useTransactionHistory", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it("returns empty transactions when no address", async () => {
    const { result } = renderHook(() => useTransactionHistory(undefined), {
      wrapper,
    });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.transactions).toEqual([]);
  });

  it("fetches transactions for a given wallet address", async () => {
    const mockData = [{ id: 1, type: "Deposit", amount: 100 }];
    (apiModule.blockchainAPI.getTransactions as jest.Mock).mockResolvedValue({
      data: mockData,
    });
    const { result } = renderHook(() => useTransactionHistory("0xabc123"), {
      wrapper,
    });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.transactions).toEqual(mockData);
    expect(result.current.error).toBeNull();
  });

  it("sets error when fetch fails", async () => {
    (apiModule.blockchainAPI.getTransactions as jest.Mock).mockRejectedValue({
      response: { status: 500, data: { detail: "Server error" } },
    });
    const { result } = renderHook(() => useTransactionHistory("0xabc123"), {
      wrapper,
    });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBeTruthy();
  });
});

describe("usePortfolioData", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it("returns null portfolioData when no address", async () => {
    const { result } = renderHook(() => usePortfolioData(undefined), {
      wrapper,
    });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.portfolioData).toBeNull();
  });

  it("fetches portfolio for a wallet address", async () => {
    const mockPortfolio = { total: 5000, tokens: [] };
    (apiModule.blockchainAPI.getPortfolio as jest.Mock).mockResolvedValue({
      data: mockPortfolio,
    });
    const { result } = renderHook(() => usePortfolioData("0xabc"), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.portfolioData).toEqual(mockPortfolio);
  });
});

describe("useEthBalance", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetches ETH balance on mount", async () => {
    (apiModule.blockchainAPI.getEthBalance as jest.Mock).mockResolvedValue({
      data: { balance: "1.5" },
    });
    const { result } = renderHook(() => useEthBalance(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.ethBalance).toBe("1.5");
  });

  it("returns refreshEthBalance function", () => {
    const { result } = renderHook(() => useEthBalance(), { wrapper });
    expect(typeof result.current.refreshEthBalance).toBe("function");
  });
});
