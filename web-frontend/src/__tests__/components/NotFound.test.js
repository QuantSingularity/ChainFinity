import { createTheme, ThemeProvider } from "@mui/material/styles";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import NotFound from "../../pages/NotFound";

const theme = createTheme();

const renderNotFound = () =>
  render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <NotFound />
      </ThemeProvider>
    </BrowserRouter>,
  );

describe("NotFound Page", () => {
  test("renders 404 heading", () => {
    renderNotFound();
    expect(screen.getByText("404")).toBeInTheDocument();
  });

  test("renders page not found message", () => {
    renderNotFound();
    expect(screen.getByText(/Page Not Found/i)).toBeInTheDocument();
  });

  test("renders back to home button", () => {
    renderNotFound();
    const button = screen.getByRole("link", { name: /Back to Home/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("href", "/");
  });

  test("renders descriptive message", () => {
    renderNotFound();
    expect(screen.getByText(/might have been removed/i)).toBeInTheDocument();
  });
});
