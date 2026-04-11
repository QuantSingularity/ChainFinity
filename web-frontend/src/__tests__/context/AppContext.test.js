import { createTheme, ThemeProvider } from "@mui/material/styles";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { AppProvider, useApp } from "../../context/AppContext";

const theme = createTheme();

// Mock api module
jest.mock("../../services/api", () => ({
  authAPI: {
    login: jest.fn(),
    register: jest.fn(),
    getCurrentUser: jest.fn(),
  },
  handleApiError: jest.fn((err) => ({
    status: err?.response?.status || 0,
    message: err?.response?.data?.detail || err?.message || "An error occurred",
  })),
}));

const { authAPI, handleApiError } = require("../../services/api");

// Test consumer component
const TestConsumer = ({ onRender }) => {
  const ctx = useApp();
  onRender && onRender(ctx);
  return (
    <div>
      <span data-testid="auth">{String(ctx.isAuthenticated)}</span>
      <span data-testid="loading">{String(ctx.loading)}</span>
      <span data-testid="darkMode">{String(ctx.darkMode)}</span>
      <span data-testid="error">{ctx.error ? ctx.error.message : "null"}</span>
      <button onClick={() => ctx.login({ email: "a@b.com", password: "pass" })}>
        Login
      </button>
      <button onClick={ctx.logout}>Logout</button>
      <button onClick={ctx.toggleTheme}>ToggleTheme</button>
      <button onClick={ctx.clearError}>ClearError</button>
    </div>
  );
};

const renderWithProviders = (ui) =>
  render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <AppProvider>{ui}</AppProvider>
      </ThemeProvider>
    </BrowserRouter>
  );

describe("AppContext", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    authAPI.getCurrentUser.mockRejectedValue(new Error("No token"));
  });

  test("provides default unauthenticated state", async () => {
    renderWithProviders(<TestConsumer />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false")
    );
    expect(screen.getByTestId("auth").textContent).toBe("false");
  });

  test("login sets isAuthenticated on success", async () => {
    const user = userEvent.setup();
    authAPI.login.mockResolvedValue({
      data: { access_token: "tok123", token_type: "Bearer" },
    });
    authAPI.getCurrentUser.mockResolvedValue({
      data: { email: "a@b.com", name: "Test" },
    });

    renderWithProviders(<TestConsumer />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false")
    );

    await user.click(screen.getByText("Login"));

    await waitFor(() =>
      expect(screen.getByTestId("auth").textContent).toBe("true")
    );
    expect(localStorage.setItem).toHaveBeenCalledWith("token", "tok123");
  });

  test("login returns false on failure", async () => {
    const user = userEvent.setup();
    authAPI.login.mockRejectedValue({ message: "Bad credentials" });
    authAPI.getCurrentUser.mockRejectedValue(new Error("No token"));

    let loginResult;
    const Capture = () => {
      const ctx = useApp();
      return (
        <button
          onClick={async () => {
            loginResult = await ctx.login({ email: "x@x.com", password: "bad" });
          }}
        >
          TryLogin
        </button>
      );
    };

    renderWithProviders(<Capture />);
    await waitFor(() => {});
    await user.click(screen.getByText("TryLogin"));
    await waitFor(() => expect(loginResult).toBe(false));
  });

  test("logout clears auth state", async () => {
    const user = userEvent.setup();
    authAPI.login.mockResolvedValue({
      data: { access_token: "tok123", token_type: "Bearer" },
    });
    authAPI.getCurrentUser.mockResolvedValue({
      data: { email: "a@b.com" },
    });

    renderWithProviders(<TestConsumer />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false")
    );

    await user.click(screen.getByText("Login"));
    await waitFor(() =>
      expect(screen.getByTestId("auth").textContent).toBe("true")
    );

    await user.click(screen.getByText("Logout"));
    expect(screen.getByTestId("auth").textContent).toBe("false");
    expect(localStorage.removeItem).toHaveBeenCalledWith("token");
  });

  test("toggleTheme changes darkMode", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestConsumer />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false")
    );

    const initialMode = screen.getByTestId("darkMode").textContent;
    await user.click(screen.getByText("ToggleTheme"));
    expect(screen.getByTestId("darkMode").textContent).not.toBe(initialMode);
  });

  test("clearError resets error state", async () => {
    const user = userEvent.setup();
    authAPI.login.mockRejectedValue({ message: "fail" });
    authAPI.getCurrentUser.mockRejectedValue(new Error("No token"));

    renderWithProviders(<TestConsumer />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false")
    );
    await user.click(screen.getByText("Login"));
    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).not.toBe("null")
    );
    await user.click(screen.getByText("ClearError"));
    expect(screen.getByTestId("error").textContent).toBe("null");
  });

  test("useApp throws when used outside provider", () => {
    const spy = jest.spyOn(console, "error").mockImplementation(() => {});
    const BadConsumer = () => {
      useApp();
      return null;
    };
    expect(() => render(<BadConsumer />)).toThrow(
      "useApp must be used within an AppProvider"
    );
    spy.mockRestore();
  });

  test("register returns success with data", async () => {
    authAPI.register.mockResolvedValue({ data: { id: 1, email: "a@b.com" } });
    authAPI.getCurrentUser.mockRejectedValue(new Error("No token"));

    let result;
    const Capture = () => {
      const ctx = useApp();
      return (
        <button
          onClick={async () => {
            result = await ctx.register({ email: "a@b.com", password: "pass" });
          }}
        >
          Register
        </button>
      );
    };

    renderWithProviders(<Capture />);
    await waitFor(() => {});
    await userEvent.setup().click(screen.getByText("Register"));
    await waitFor(() => expect(result?.success).toBe(true));
  });
});
