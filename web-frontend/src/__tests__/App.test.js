import { createTheme, ThemeProvider } from "@mui/material/styles";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import App from "../App";
import { AppProvider } from "../context/AppContext";

// Mock the AppContext
jest.mock("../context/AppContext", () => ({
  ...jest.requireActual("../context/AppContext"),
  useApp: () => ({
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null,
    darkMode: false,
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    clearError: jest.fn(),
    toggleTheme: jest.fn(),
  }),
}));

const theme = createTheme();

const renderWithProviders = (component) => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <AppProvider>{component}</AppProvider>
      </ThemeProvider>
    </BrowserRouter>,
  );
};

describe("App Component", () => {
  test("renders without crashing", () => {
    renderWithProviders(<App />);
    expect(document.querySelector("main")).toBeInTheDocument();
  });

  test("renders Navbar component", () => {
    renderWithProviders(<App />);
    expect(screen.getByText(/ChainFinity/i)).toBeInTheDocument();
  });

  test("renders Footer component", () => {
    renderWithProviders(<App />);
    expect(screen.getByText(/All rights reserved/i)).toBeInTheDocument();
  });

  test("renders Home page by default", () => {
    renderWithProviders(<App />);
    expect(
      screen.getByText(/Track Your Crypto Portfolio with Ease/i),
    ).toBeInTheDocument();
  });
});
