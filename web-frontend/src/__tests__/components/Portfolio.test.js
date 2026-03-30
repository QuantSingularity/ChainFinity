import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import Portfolio from "../../components/Portfolio";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const TestWrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe("Portfolio Component", () => {
  const mockPortfolioData = {
    tokens: [
      { symbol: "ETH", balance: "1.5", value: "3000" },
      { symbol: "USDT", balance: "1000", value: "1000" },
    ],
    totalValue: "4000",
  };

  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  test("renders portfolio data correctly", async () => {
    // Mock the API response
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve(mockPortfolioData),
        ok: true,
      }),
    );

    render(
      <TestWrapper>
        <Portfolio />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("Total Value: $4,000.00")).toBeInTheDocument();
      expect(screen.getByText("ETH")).toBeInTheDocument();
      expect(screen.getByText("USDT")).toBeInTheDocument();
      expect(screen.getByText("1.5")).toBeInTheDocument();
      expect(screen.getByText("1000")).toBeInTheDocument();
    });
  });

  test("handles empty portfolio", async () => {
    // Mock empty portfolio response
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ tokens: [], totalValue: "0" }),
        ok: true,
      }),
    );

    render(
      <TestWrapper>
        <Portfolio />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("Total Value: $0.00")).toBeInTheDocument();
      expect(screen.getByText("No tokens found")).toBeInTheDocument();
    });
  });

  test("handles API errors gracefully", async () => {
    // Mock API error
    global.fetch = jest.fn(() => Promise.reject(new Error("API Error")));

    render(
      <TestWrapper>
        <Portfolio />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("Error loading portfolio")).toBeInTheDocument();
    });
  });

  test("handles network errors gracefully", async () => {
    // Mock network error
    global.fetch = jest.fn(() => Promise.reject(new Error("Network Error")));

    render(
      <TestWrapper>
        <Portfolio />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("Network error occurred")).toBeInTheDocument();
    });
  });

  test("refreshes data when refresh button is clicked", async () => {
    // Mock the API response
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve(mockPortfolioData),
        ok: true,
      }),
    );

    render(
      <TestWrapper>
        <Portfolio />
      </TestWrapper>,
    );

    const refreshButton = screen.getByRole("button", { name: /refresh/i });
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2); // Initial load + refresh
    });
  });

  test("sorts tokens by value when sort button is clicked", async () => {
    // Mock the API response
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve(mockPortfolioData),
        ok: true,
      }),
    );

    render(
      <TestWrapper>
        <Portfolio />
      </TestWrapper>,
    );

    const sortButton = screen.getByRole("button", { name: /sort by value/i });
    fireEvent.click(sortButton);

    await waitFor(() => {
      const tokenRows = screen.getAllByRole("row");
      // Check if ETH (higher value) appears before USDT
      expect(tokenRows[1]).toHaveTextContent("ETH");
      expect(tokenRows[2]).toHaveTextContent("USDT");
    });
  });

  test("filters tokens by search input", async () => {
    // Mock the API response
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve(mockPortfolioData),
        ok: true,
      }),
    );

    render(
      <TestWrapper>
        <Portfolio />
      </TestWrapper>,
    );

    const searchInput = screen.getByPlaceholderText(/search tokens/i);
    fireEvent.change(searchInput, { target: { value: "ETH" } });

    await waitFor(() => {
      expect(screen.getByText("ETH")).toBeInTheDocument();
      expect(screen.queryByText("USDT")).not.toBeInTheDocument();
    });
  });

  test("displays loading state while fetching data", async () => {
    // Mock delayed API response
    global.fetch = jest.fn(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                json: () => Promise.resolve(mockPortfolioData),
                ok: true,
              }),
            100,
          ),
        ),
    );

    render(
      <TestWrapper>
        <Portfolio />
      </TestWrapper>,
    );

    expect(screen.getByText("Loading...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
    });
  });
});
