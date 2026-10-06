import { fireEvent, render, waitFor } from "@testing-library/react-native";
import React from "react";
import RiskScreen, { correlationColor, formatPercent } from "../../app/risk";
import { aiAPI, portfolioAPI, riskAPI } from "../services/api";

let mockAuthenticated = true;

jest.mock("../context/AppContext", () => ({
  useApp: () => ({ isAuthenticated: mockAuthenticated }),
}));

jest.mock("../services/api", () => {
  const actual = jest.requireActual("../services/api");
  return {
    ...actual,
    portfolioAPI: { list: jest.fn() },
    aiAPI: { getStatus: jest.fn(), getPortfolioInsights: jest.fn() },
    riskAPI: { assess: jest.fn(), listAssessments: jest.fn() },
  };
});

const insights = {
  portfolio_id: "p1",
  generated_at: "2026-01-01T00:00:00Z",
  assets: ["BTC", "ETH"],
  volatility: {
    BTC: {
      symbol: "BTC",
      predicted_vol: 0.55,
      predicted_vol_std: null,
      confidence_interval: null,
      vol_bucket: "medium",
      confidence: null,
      recent_realized_vol: 0.5,
      forecast_horizon_days: 7,
      model: "ewma_fallback",
    },
  },
  correlation: {
    assets: ["BTC", "ETH"],
    matrix: [
      [1, 0.8],
      [0.8, 1],
    ],
    model: "ledoit_wolf_shrinkage",
  },
  warnings: ["No market history available for SOL"],
};

describe("RiskScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAuthenticated = true;
    (portfolioAPI.list as jest.Mock).mockResolvedValue({
      data: { items: [{ id: "p1", name: "Main" }] },
    });
    (aiAPI.getStatus as jest.Mock).mockResolvedValue({
      data: { models: { volatility: { loaded: false, mode: "fallback" } } },
    });
    (aiAPI.getPortfolioInsights as jest.Mock).mockResolvedValue({
      data: insights,
    });
    (riskAPI.listAssessments as jest.Mock).mockResolvedValue({ data: [] });
  });

  it("prompts unauthenticated users to sign in", () => {
    mockAuthenticated = false;
    const { getByText } = render(<RiskScreen />);
    expect(getByText("Sign in required")).toBeTruthy();
  });

  it("renders forecasts, correlations and warnings", async () => {
    const { findByText, getAllByText } = render(<RiskScreen />);
    expect(await findByText("55.0%")).toBeTruthy();
    expect(await findByText("medium")).toBeTruthy();
    expect(
      await findByText("No market history available for SOL"),
    ).toBeTruthy();
    expect(getAllByText("0.80")).toHaveLength(2);
    expect(aiAPI.getPortfolioInsights).toHaveBeenCalledWith("p1", 7);
  });

  it("runs an assessment and shows the score", async () => {
    (riskAPI.assess as jest.Mock).mockResolvedValue({
      data: {
        id: "a1",
        risk_score: 47.5,
        risk_level: "medium",
        action_required: false,
        recommendations: ["Diversify"],
        stress_tests: [
          {
            scenario_name: "Market Crash",
            status: "completed",
            potential_loss_percent: 54,
          },
        ],
      },
    });
    const { findByText } = render(<RiskScreen />);
    fireEvent.press(await findByText("Run assessment"));
    expect(await findByText("47.5")).toBeTruthy();
    expect(await findByText("Diversify")).toBeTruthy();
    expect(await findByText("54.0%")).toBeTruthy();
  });

  it("shows the backend error when market data is unavailable", async () => {
    (aiAPI.getPortfolioInsights as jest.Mock).mockRejectedValue({
      response: {
        status: 503,
        data: { detail: "Insufficient market history" },
      },
    });
    const { findByText } = render(<RiskScreen />);
    expect(await findByText("Insufficient market history")).toBeTruthy();
  });

  it("prompts to create a portfolio when none exist", async () => {
    (portfolioAPI.list as jest.Mock).mockResolvedValue({ data: { items: [] } });
    const { findByText } = render(<RiskScreen />);
    await waitFor(async () =>
      expect(await findByText("No portfolios")).toBeTruthy(),
    );
  });
});

describe("risk helpers", () => {
  it("formats percentages defensively", () => {
    expect(formatPercent(0.1234)).toBe("12.3%");
    expect(formatPercent(null)).toBe("n/a");
    expect(formatPercent(Number.NaN)).toBe("n/a");
  });

  it("maps correlation sign to colour", () => {
    expect(correlationColor(5)).toBe(correlationColor(1));
    expect(correlationColor(0.5)).toContain("239, 68, 68");
    expect(correlationColor(-0.5)).toContain("56, 189, 248");
  });
});
