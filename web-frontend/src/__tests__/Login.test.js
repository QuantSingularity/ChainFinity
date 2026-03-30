import { createTheme, ThemeProvider } from "@mui/material/styles";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { AppProvider } from "../context/AppContext";
import Login from "../pages/Login";

const theme = createTheme();

// Mock useApp hook
const mockLogin = jest.fn();
const mockClearError = jest.fn();

jest.mock("../context/AppContext", () => ({
  ...jest.requireActual("../context/AppContext"),
  useApp: () => ({
    login: mockLogin,
    error: null,
    loading: false,
    clearError: mockClearError,
  }),
}));

const renderLogin = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <AppProvider>
          <Login />
        </AppProvider>
      </ThemeProvider>
    </BrowserRouter>,
  );
};

describe("Login Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders login form", () => {
    renderLogin();
    expect(screen.getByText(/Welcome Back/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Sign In/i }),
    ).toBeInTheDocument();
  });

  test("shows error when submitting empty form", async () => {
    const user = userEvent.setup();
    renderLogin();

    const submitButton = screen.getByRole("button", { name: /Sign In/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/Please enter both email and password/i),
      ).toBeInTheDocument();
    });
  });

  test("calls login function with correct credentials", async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValue(true);

    renderLogin();

    const emailInput = screen.getByLabelText(/Email Address/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const submitButton = screen.getByRole("button", { name: /Sign In/i });

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "password123");
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: "test@example.com",
        password: "password123",
      });
    });
  });

  test("displays link to register page", () => {
    renderLogin();
    const registerLink = screen.getByText(/Sign Up/i);
    expect(registerLink).toBeInTheDocument();
    expect(registerLink.closest("a")).toHaveAttribute("href", "/register");
  });

  test("toggles password visibility", async () => {
    const user = userEvent.setup();
    renderLogin();

    const passwordInput = screen.getByLabelText(/Password/i);
    expect(passwordInput).toHaveAttribute("type", "password");

    const toggleButton = screen.getByLabelText(/toggle password visibility/i);
    await user.click(toggleButton);

    expect(passwordInput).toHaveAttribute("type", "text");
  });
});
