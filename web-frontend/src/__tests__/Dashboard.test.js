import { createTheme, ThemeProvider } from "@mui/material/styles";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { AppProvider } from "../context/AppContext";
import Dashboard from "../pages/Dashboard";

const theme = createTheme();

// Mock hooks
jest.mock("../hooks/useProtocolData", () => ({
  usePortfolioData: () => ({
    portfolioData: {
      total_value: "12500.00",
      assets: [
        { symbol: "ETH", balance: "5.0", value_usd: "2000", name: "Ethereum" },
        { symbol: "BTC", balance: "0.5", value_usd: "25000", name: "Bitcoin" },
      ],
    },
    loading: false,
    error: null,
    refreshPortfolio: jest.fn(),
  }),
  useTransactionHistory: () => ({
    transactions: [
      {
        id: 1,
        type: "receive",
        asset: "ETH",
        amount: "1.0 ETH",
        value: "$2,000",
        status: "Completed",
      },
      {
        id: 2,
        type: "send",
        asset: "BTC",
        amount: "0.1 BTC",
        value: "$2,500",
        status: "Completed",
      },
    ],
    loading: false,
    error: null,
    refreshTransactions: jest.fn(),
  }),
}));

jest.mock("../context/AppContext", () => ({
  ...jest.requireActual("../context/AppContext"),
  useApp: () => ({
    user: { email: "test@example.com", wallet_address: "0x123456" },
    isAuthenticated: true,
    loading: false,
  }),
}));

const renderDashboard = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <AppProvider>
          <Dashboard />
        </AppProvider>
      </ThemeProvider>
    </BrowserRouter>,
  );
};

describe("Dashboard Component", () => {
  test("renders dashboard header", () => {
    renderDashboard();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
  });

  test("displays portfolio value", () => {
    renderDashboard();
    expect(screen.getByText(/Portfolio Value/i)).toBeInTheDocument();
    expect(screen.getByText("$12500.00")).toBeInTheDocument();
  });

  test("displays asset allocation", () => {
    renderDashboard();
    expect(screen.getByText(/Asset Allocation/i)).toBeInTheDocument();
  });

  test("displays assets list", () => {
    renderDashboard();
    expect(screen.getByText("ETH")).toBeInTheDocument();
    expect(screen.getByText("BTC")).toBeInTheDocument();
  });

  test("displays transactions", () => {
    renderDashboard();
    // Click on transactions tab
    const transactionsTab = screen.getByText("Recent Transactions");
    expect(transactionsTab).toBeInTheDocument();
  });

  test("renders refresh button", () => {
    renderDashboard();
    const refreshButton = screen.getByRole("button", { name: /Refresh/i });
    expect(refreshButton).toBeInTheDocument();
  });
});
