import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { useRouter } from "next/navigation";
import Login from "@/app/login/page";
import { useApp } from "@/context/AppContext";

// Mock Next.js router
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

// Mock AppContext
jest.mock("@/context/AppContext", () => ({
  useApp: jest.fn(),
}));

describe("Login Page", () => {
  const mockPush = jest.fn();
  const mockLogin = jest.fn();
  const mockClearError = jest.fn();
  const mockConnectWallet = jest.fn();

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
    (useApp as jest.Mock).mockReturnValue({
      actions: {
        login: mockLogin,
        clearError: mockClearError,
        connectWallet: mockConnectWallet,
      },
      error: null,
      loading: false,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("renders login form", () => {
    render(<Login />);
    expect(screen.getByText("Welcome Back")).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
  });

  it("shows validation error when fields are empty", async () => {
    render(<Login />);
    const submitButton = screen.getByRole("button", { name: /sign in/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/please enter both email and password/i),
      ).toBeInTheDocument();
    });
  });

  it("calls login function with correct credentials", async () => {
    mockLogin.mockResolvedValue(true);
    render(<Login />);

    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/^password$/i);
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: "test@example.com",
        password: "password123",
      });
    });
  });

  it("redirects to dashboard on successful login", async () => {
    mockLogin.mockResolvedValue(true);
    render(<Login />);

    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/^password$/i);
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("toggles password visibility", () => {
    render(<Login />);
    const passwordInput = screen.getByLabelText(
      /^password$/i,
    ) as HTMLInputElement;
    const toggleButton = screen.getByRole("button", {
      name: /toggle password visibility/i,
    });

    expect(passwordInput.type).toBe("password");
    fireEvent.click(toggleButton);
    expect(passwordInput.type).toBe("text");
  });
});
