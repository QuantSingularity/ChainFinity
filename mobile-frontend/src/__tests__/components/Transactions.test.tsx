import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import TransactionsPage from "@/app/transactions/page";
import { useTransactionHistory } from "@/hooks/useProtocolData";

jest.mock("@/hooks/useProtocolData", () => ({
  useTransactionHistory: jest.fn(),
}));

const mockRefresh = jest.fn();
const mockTransactions = [
  {
    id: 1,
    type: "Deposit",
    amount: 500,
    date: "2024-10-01",
    status: "Completed",
  },
  {
    id: 2,
    type: "Withdrawal",
    amount: 200,
    date: "2024-10-10",
    status: "Pending",
  },
  { id: 3, type: "Bridge", amount: 1000, date: "2024-10-14", status: "Failed" },
];

beforeEach(() => {
  jest.clearAllMocks();
  (useTransactionHistory as jest.Mock).mockReturnValue({
    transactions: mockTransactions,
    loading: false,
    error: null,
    refreshTransactions: mockRefresh,
  });
});

describe("TransactionsPage", () => {
  it("renders the heading", () => {
    render(<TransactionsPage />);
    expect(screen.getByText("Transactions")).toBeInTheDocument();
  });

  it("renders transaction list", () => {
    render(<TransactionsPage />);
    expect(screen.getByText("Deposit")).toBeInTheDocument();
    expect(screen.getByText("Withdrawal")).toBeInTheDocument();
    expect(screen.getByText("Bridge")).toBeInTheDocument();
  });

  it("shows transaction amounts", () => {
    render(<TransactionsPage />);
    expect(screen.getByText("+$500")).toBeInTheDocument();
    expect(screen.getByText("-$200")).toBeInTheDocument();
  });

  it("renders status badges", () => {
    render(<TransactionsPage />);
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("shows loading skeletons when loading", () => {
    (useTransactionHistory as jest.Mock).mockReturnValue({
      transactions: [],
      loading: true,
      error: null,
      refreshTransactions: mockRefresh,
    });
    render(<TransactionsPage />);
    expect(screen.queryByText("Deposit")).not.toBeInTheDocument();
  });

  it("shows error message when error occurs", () => {
    (useTransactionHistory as jest.Mock).mockReturnValue({
      transactions: [],
      loading: false,
      error: "Failed to fetch transactions",
      refreshTransactions: mockRefresh,
    });
    render(<TransactionsPage />);
    expect(
      screen.getByText(/failed to fetch transactions/i),
    ).toBeInTheDocument();
  });

  it("shows empty state message when no transactions", () => {
    (useTransactionHistory as jest.Mock).mockReturnValue({
      transactions: [],
      loading: false,
      error: null,
      refreshTransactions: mockRefresh,
    });
    render(<TransactionsPage />);
    expect(screen.getByText(/no transactions found/i)).toBeInTheDocument();
  });

  it("calls refreshTransactions on refresh button click", async () => {
    render(<TransactionsPage />);
    const refreshBtn = screen.getByRole("button", { name: /refresh/i });
    fireEvent.click(refreshBtn);
    await waitFor(() => expect(mockRefresh).toHaveBeenCalled());
  });
});
