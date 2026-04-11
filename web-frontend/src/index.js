import CssBaseline from "@mui/material/CssBaseline";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AppProvider, useApp } from "./context/AppContext";
import "./styles/globalStyles";

const getTheme = (mode) =>
  createTheme({
    palette: {
      mode,
      primary: {
        main: "#6c63ff",
        light: "#8f88ff",
        dark: "#4b44cc",
        contrastText: "#ffffff",
      },
      secondary: {
        main: "#03dac6",
        light: "#66fff8",
        dark: "#00a896",
        contrastText: "#000000",
      },
      background: {
        default: mode === "light" ? "#f8f9fa" : "#0f0f17",
        paper: mode === "light" ? "#ffffff" : "#1a1a2e",
      },
      ...(mode === "dark" && {
        text: {
          primary: "#e8e8f0",
          secondary: "#a0a0b8",
        },
      }),
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h1: { fontWeight: 700 },
      h2: { fontWeight: 700 },
      h3: { fontWeight: 600 },
      h4: { fontWeight: 600 },
      h5: { fontWeight: 600 },
      h6: { fontWeight: 600 },
      button: { fontWeight: 600, textTransform: "none" },
    },
    shape: { borderRadius: 12 },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            padding: "10px 24px",
            boxShadow: "none",
            "&:hover": { boxShadow: "0px 4px 8px rgba(0, 0, 0, 0.15)" },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            boxShadow:
              mode === "light"
                ? "0px 4px 20px rgba(0, 0, 0, 0.05)"
                : "0px 4px 20px rgba(0, 0, 0, 0.3)",
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: "none",
          },
        },
      },
    },
  });

const ThemedApp = () => {
  const { darkMode } = useApp();
  const theme = getTheme(darkMode ? "dark" : "light");

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <App />
      </LocalizationProvider>
    </ThemeProvider>
  );
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <AppProvider>
        <ThemedApp />
      </AppProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
