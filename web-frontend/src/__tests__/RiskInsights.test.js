import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import RiskInsights, {
  correlationColor,
  formatPercent,
} from "../pages/RiskInsights";
import { aiAPI, portfolioAPI, riskAPI } from "../services/api";

jest.mock("../services/api", () => ({
  aiAPI: {
    getStatus: jest.fn(),
    getPortfolioInsights: jest.fn(),
  },
  portfolioAPI: { list: jest.fn() },
  riskAPI: { assess: jest.fn(), listAssessments: jest.fn() },
  handleApiError: (error) => ({
    status: error?.response?.status || 0,
    message: error?.response?.data?.detail || "An error occurred",
  }),
}));

const theme = createTheme();
const renderPage = () =>
  render(
    <ThemeProvider theme={theme}>
      <RiskInsights />
    </ThemeProvider>,
  );

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

describe("RiskInsights", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    portfolioAPI.list.mockResolvedValue({
      data: { items: [{ id: "p1", name: "Main" }] },
    });
    aiAPI.getStatus.mockResolvedValue({
      data: {
        models: {
          volatility: { loaded: false, mode: "fallback" },
          liquidity: { loaded: true, mode: "rule_based" },
        },
      },
    });
    aiAPI.getPortfolioInsights.mockResolvedValue({ data: insights });
    riskAPI.listAssessments.mockResolvedValue({ data: [] });
  });

  test("renders forecasts, correlations, warnings and model status", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText("55.0%")).toBeInTheDocument());
    expect(screen.getByText("medium")).toBeInTheDocument();
    expect(screen.getByLabelText("correlation matrix")).toBeInTheDocument();
    expect(screen.getAllByText("0.80", { selector: "td" })).toHaveLength(2);
    expect(
      screen.getByText("No market history available for SOL"),
    ).toBeInTheDocument();
    expect(screen.getByText(/Volatility: fallback/)).toBeInTheDocument();
    expect(aiAPI.getPortfolioInsights).toHaveBeenCalledWith("p1", 7);
  });

  test("runs an assessment and shows the result", async () => {
    riskAPI.assess.mockResolvedValue({
      data: {
        risk_score: 47.5,
        risk_level: "medium",
        risk_grade: "Medium",
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
    renderPage();
    const button = await screen.findByRole("button", {
      name: /run assessment/i,
    });
    fireEvent.click(button);
    await waitFor(() => expect(screen.getByText("47.5")).toBeInTheDocument());
    expect(screen.getByText("Diversify")).toBeInTheDocument();
    expect(screen.getByText("54.0%")).toBeInTheDocument();
  });

  test("shows the backend error when market data is unavailable", async () => {
    aiAPI.getPortfolioInsights.mockRejectedValue({
      response: {
        status: 503,
        data: { detail: "Insufficient market history" },
      },
    });
    renderPage();
    await waitFor(() =>
      expect(
        screen.getByText("Insufficient market history"),
      ).toBeInTheDocument(),
    );
  });

  test("prompts to create a portfolio when none exist", async () => {
    portfolioAPI.list.mockResolvedValue({ data: { items: [] } });
    renderPage();
    await waitFor(() =>
      expect(screen.getByText(/Create a portfolio/)).toBeInTheDocument(),
    );
  });
});

describe("risk helpers", () => {
  test("formatPercent handles invalid values", () => {
    expect(formatPercent(0.1234)).toBe("12.3%");
    expect(formatPercent(null)).toBe("n/a");
    expect(formatPercent(NaN)).toBe("n/a");
  });

  test("correlationColor clamps and distinguishes sign", () => {
    expect(correlationColor(2)).toBe(correlationColor(1));
    expect(correlationColor(0.5)).toContain("239, 68, 68");
    expect(correlationColor(-0.5)).toContain("56, 189, 248");
  });
});
