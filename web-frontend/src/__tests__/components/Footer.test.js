import { createTheme, ThemeProvider } from "@mui/material/styles";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import Footer from "../../components/layout/Footer";

const theme = createTheme();

const renderFooter = () =>
  render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <Footer />
      </ThemeProvider>
    </BrowserRouter>,
  );

describe("Footer Component", () => {
  test("renders ChainFinity brand name", () => {
    renderFooter();
    expect(screen.getByText("ChainFinity")).toBeInTheDocument();
  });

  test("renders current year in copyright", () => {
    renderFooter();
    const year = new Date().getFullYear().toString();
    expect(screen.getByText(new RegExp(year))).toBeInTheDocument();
  });

  test("renders all rights reserved text", () => {
    renderFooter();
    expect(screen.getByText(/All rights reserved/i)).toBeInTheDocument();
  });

  test("renders Product section links", () => {
    renderFooter();
    expect(screen.getByText("Product")).toBeInTheDocument();
    expect(screen.getByText("Features")).toBeInTheDocument();
    expect(screen.getByText("Pricing")).toBeInTheDocument();
  });

  test("renders Resources section links", () => {
    renderFooter();
    expect(screen.getByText("Resources")).toBeInTheDocument();
    expect(screen.getByText("Documentation")).toBeInTheDocument();
  });

  test("renders Company section links", () => {
    renderFooter();
    expect(screen.getByText("Company")).toBeInTheDocument();
    expect(screen.getByText("About")).toBeInTheDocument();
  });

  test("renders social media buttons", () => {
    renderFooter();
    expect(screen.getByLabelText("github")).toBeInTheDocument();
    expect(screen.getByLabelText("twitter")).toBeInTheDocument();
    expect(screen.getByLabelText("linkedin")).toBeInTheDocument();
    expect(screen.getByLabelText("telegram")).toBeInTheDocument();
  });

  test("renders privacy and terms links", () => {
    renderFooter();
    expect(screen.getByText("Privacy")).toBeInTheDocument();
    expect(screen.getByText("Terms")).toBeInTheDocument();
  });
});
