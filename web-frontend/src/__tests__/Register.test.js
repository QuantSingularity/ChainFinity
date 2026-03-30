import { createTheme, ThemeProvider } from "@mui/material/styles";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { AppProvider } from "../context/AppContext";
import Register from "../pages/Register";

const theme = createTheme();

// Mock useApp hook
const mockRegister = jest.fn();
const mockClearError = jest.fn();

jest.mock("../context/AppContext", () => ({
  ...jest.requireActual("../context/AppContext"),
  useApp: () => ({
    register: mockRegister,
    error: null,
    loading: false,
    clearError: mockClearError,
  }),
}));

const renderRegister = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <AppProvider>
          <Register />
        </AppProvider>
      </ThemeProvider>
    </BrowserRouter>,
  );
};

describe("Register Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders registration form", () => {
    renderRegister();
    expect(screen.getByText(/Create Account/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Full Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getAllByLabelText(/Password/i)[0]).toBeInTheDocument();
  });

  test("shows error when passwords do not match", async () => {
    const user = userEvent.setup();
    renderRegister();

    await user.type(screen.getByLabelText(/Full Name/i), "John Doe");
    await user.type(
      screen.getByLabelText(/Email Address/i),
      "john@example.com",
    );
    await user.type(screen.getAllByLabelText(/Password/i)[0], "password123");
    await user.type(
      screen.getByLabelText(/Confirm Password/i),
      "differentpassword",
    );

    const submitButton = screen.getByRole("button", {
      name: /Create Account/i,
    });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument();
    });
  });

  test("shows error for short password", async () => {
    const user = userEvent.setup();
    renderRegister();

    await user.type(screen.getByLabelText(/Full Name/i), "John Doe");
    await user.type(
      screen.getByLabelText(/Email Address/i),
      "john@example.com",
    );
    await user.type(screen.getAllByLabelText(/Password/i)[0], "short");
    await user.type(screen.getByLabelText(/Confirm Password/i), "short");

    const submitButton = screen.getByRole("button", {
      name: /Create Account/i,
    });
    await user.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/Password must be at least 8 characters long/i),
      ).toBeInTheDocument();
    });
  });

  test("calls register function with correct data", async () => {
    const user = userEvent.setup();
    mockRegister.mockResolvedValue({ success: true });

    renderRegister();

    await user.type(screen.getByLabelText(/Full Name/i), "John Doe");
    await user.type(
      screen.getByLabelText(/Email Address/i),
      "john@example.com",
    );
    await user.type(screen.getAllByLabelText(/Password/i)[0], "password123");
    await user.type(screen.getByLabelText(/Confirm Password/i), "password123");

    const submitButton = screen.getByRole("button", {
      name: /Create Account/i,
    });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        name: "John Doe",
        email: "john@example.com",
        password: "password123",
        wallet_address: undefined,
      });
    });
  });
});
