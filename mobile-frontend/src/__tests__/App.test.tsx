import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type React from "react";
import App from "../App";
import "@testing-library/jest-dom";

// Create a new QueryClient for testing
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

// Wrapper component to provide necessary context
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

// Mock the next/router
jest.mock("next/router", () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: "/",
  }),
}));

// Mock global fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe("Mobile App Component", () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  test("renders login screen by default", () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>,
    );

    expect(screen.getByText(/welcome/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
  });

  test("handles login form submission", async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>,
    );

    const emailInput = screen.getByPlaceholderText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      // Add assertions based on your login success behavior
      expect(screen.queryByText(/welcome/i)).not.toBeInTheDocument();
    });
  });

  test("validates login form inputs", async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>,
    );

    const emailInput = screen.getByPlaceholderText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    // Test invalid email
    fireEvent.change(emailInput, { target: { value: "invalid-email" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
    });

    // Test short password
    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "short" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/password must be at least 8 characters/i),
      ).toBeInTheDocument();
    });
  });

  test("handles wallet connection", async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>,
    );

    const connectWalletButton = screen.getByRole("button", {
      name: /connect wallet/i,
    });
    fireEvent.click(connectWalletButton);

    await waitFor(() => {
      // Add assertions based on your wallet connection behavior
      expect(screen.getByText(/wallet connected/i)).toBeInTheDocument();
    });
  });

  test("displays portfolio data after successful login", async () => {
    // Mock successful login
    const mockPortfolioData = {
      tokens: [
        { symbol: "ETH", balance: "1.5", value: "3000" },
        { symbol: "USDT", balance: "1000", value: "1000" },
      ],
    };

    // Mock the API response
    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve(mockPortfolioData),
      ok: true,
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>,
    );

    // Perform login
    const emailInput = screen.getByPlaceholderText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("ETH")).toBeInTheDocument();
      expect(screen.getByText("USDT")).toBeInTheDocument();
      expect(screen.getByText("1.5")).toBeInTheDocument();
      expect(screen.getByText("1000")).toBeInTheDocument();
    });
  });

  test("handles API errors gracefully", async () => {
    // Mock API error
    mockFetch.mockRejectedValueOnce(new Error("API Error"));

    render(
      <TestWrapper>
        <App />
      </TestWrapper>,
    );

    // Perform login
    const emailInput = screen.getByPlaceholderText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/error occurred/i)).toBeInTheDocument();
    });
  });

  test("handles network errors gracefully", async () => {
    // Mock network error
    mockFetch.mockRejectedValueOnce(new Error("Network Error"));

    render(
      <TestWrapper>
        <App />
      </TestWrapper>,
    );

    // Perform login
    const emailInput = screen.getByPlaceholderText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  test("handles biometric authentication", async () => {
    // Mock biometric authentication
    const mockBiometricAuth = jest.fn().mockResolvedValue(true);
    Object.defineProperty(window.navigator, "credentials", {
      value: {
        get: mockBiometricAuth,
      },
      writable: true,
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>,
    );

    const biometricButton = screen.getByRole("button", {
      name: /use biometrics/i,
    });
    fireEvent.click(biometricButton);

    await waitFor(() => {
      expect(mockBiometricAuth).toHaveBeenCalled();
      expect(screen.queryByText(/welcome/i)).not.toBeInTheDocument();
    });
  });

  test("handles offline mode", async () => {
    // Mock offline status
    Object.defineProperty(window.navigator, "onLine", {
      value: false,
      writable: true,
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>,
    );

    const emailInput = screen.getByPlaceholderText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/you are offline/i)).toBeInTheDocument();
    });
  });
});
