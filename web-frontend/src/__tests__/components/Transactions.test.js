import { createTheme, ThemeProvider } from "@mui/material/styles";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import Transactions from "../../pages/Transactions";

jest.mock("../../context/AppContext", () => ({
  ...jest.requireActual("../../context/AppContext"),
  useApp: () => ({
    user: { email: "test@example.com", wallet_address: "0xabc123" },
    isAuthenticated: true,
    loading: false,
  }),
}));

jest.mock("../../hooks/useProtocolData", () => ({
  useTransactionHistory: () => ({
    transactions: [
      {
        id: "tx1",
        hash: "0xhash1",
        type: "send",
        asset: "ETH",
        amount: "1.5",
        value_usd: "3000",
        status: "Completed",
        network: "ethereum",
        timestamp: 1700000000,
        from: "0xAAA",
        to: "0xBBB",
      },
      {
        id: "tx2",
        hash: "0xhash2",
        type: "receive",
        asset: "USDT",
        amount: "500",
        value_usd: "500",
        status: "Pending",
        network: "polygon",
        timestamp: 1700001000,
        from: "0xCCC",
        to: "0xDDD",
      },
    ],
    loading: false,
    error: null,
    refreshTransactions: jest.fn(),
  }),
}));

const theme = createTheme();

const renderTransactions = () =>
  render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <Transactions />
      </ThemeProvider>
    </BrowserRouter>
  );

describe("Transactions Page", () => {
  test("renders page heading", () => {
    renderTransactions();
    expect(screen.getByText(/Transaction/i)).toBeInTheDocument();
  });

  test("renders transaction table headers", () => {
    renderTransactions();
    expect(screen.getByText(/Type/i)).toBeInTheDocument();
    expect(screen.getByText(/Asset/i)).toBeInTheDocument();
    expect(screen.getByText(/Status/i)).toBeInTheDocument();
  });

  test("renders transaction rows", () => {
    renderTransactions();
    expect(screen.getByText("ETH")).toBeInTheDocument();
    expect(screen.getByText("USDT")).toBeInTheDocument();
  });

  test("renders search input", () => {
    renderTransactions();
    const searchInput = screen.getByPlaceholderText(/Search/i);
    expect(searchInput).toBeInTheDocument();
  });

  test("search filters transactions", async () => {
    const user = userEvent.setup();
    renderTransactions();
    const searchInput = screen.getByPlaceholderText(/Search/i);
    await user.type(searchInput, "ETH");
    await waitFor(() => {
      expect(screen.getByText("ETH")).toBeInTheDocument();
    });
  });

  test("renders refresh button", () => {
    renderTransactions();
    const refreshBtn = screen.getByRole("button", { name: /Refresh/i });
    expect(refreshBtn).toBeInTheDocument();
  });

  test("renders type filter", () => {
    renderTransactions();
    expect(screen.getByLabelText(/Type/i)).toBeInTheDocument();
  });
});
