import { createTheme, ThemeProvider } from "@mui/material/styles";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import Settings from "../../pages/Settings";

jest.mock("../../context/AppContext", () => ({
  ...jest.requireActual("../../context/AppContext"),
  useApp: () => ({
    user: {
      name: "John Doe",
      email: "john@example.com",
      wallet_address: "0x1234567890abcdef1234567890abcdef12345678",
    },
    isAuthenticated: true,
    darkMode: false,
    toggleTheme: jest.fn(),
  }),
}));

const theme = createTheme();

const renderSettings = () =>
  render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <Settings />
      </ThemeProvider>
    </BrowserRouter>
  );

describe("Settings Page", () => {
  test("renders settings page title", () => {
    renderSettings();
    expect(screen.getByText(/Settings/i)).toBeInTheDocument();
  });

  test("renders all tabs", () => {
    renderSettings();
    expect(screen.getByRole("tab", { name: /Profile/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Security/i })).toBeInTheDocument();
    expect(
      screen.getByRole("tab", { name: /Notifications/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("tab", { name: /Preferences/i })
    ).toBeInTheDocument();
  });

  test("renders profile form by default", () => {
    renderSettings();
    expect(screen.getByDisplayValue("John Doe")).toBeInTheDocument();
    expect(
      screen.getByDisplayValue("john.doe@example.com")
    ).toBeInTheDocument();
  });

  test("switches to Security tab on click", async () => {
    const user = userEvent.setup();
    renderSettings();
    await user.click(screen.getByRole("tab", { name: /Security/i }));
    await waitFor(() => {
      expect(
        screen.getByLabelText(/Current Password/i)
      ).toBeInTheDocument();
    });
  });

  test("switches to Notifications tab", async () => {
    const user = userEvent.setup();
    renderSettings();
    await user.click(screen.getByRole("tab", { name: /Notifications/i }));
    await waitFor(() => {
      expect(screen.getByText(/Email Notifications/i)).toBeInTheDocument();
    });
  });

  test("switches to Preferences tab", async () => {
    const user = userEvent.setup();
    renderSettings();
    await user.click(screen.getByRole("tab", { name: /Preferences/i }));
    await waitFor(() => {
      expect(screen.getByText(/Appearance/i)).toBeInTheDocument();
    });
  });

  test("profile form accepts input", async () => {
    const user = userEvent.setup();
    renderSettings();
    const nameField = screen.getByDisplayValue("John Doe");
    await user.clear(nameField);
    await user.type(nameField, "Jane Smith");
    expect(nameField).toHaveValue("Jane Smith");
  });

  test("renders save changes button", () => {
    renderSettings();
    expect(
      screen.getAllByRole("button", { name: /Save/i }).length
    ).toBeGreaterThan(0);
  });
});
