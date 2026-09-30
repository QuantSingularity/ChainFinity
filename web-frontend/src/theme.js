// theme.js - kept for backward compatibility.
// The active theme is created dynamically in src/index.js (getTheme).
// Importing this file directly is deprecated; use the ThemeProvider from index.js.

import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    primary: {
      main: "#6c63ff",
      light: "#8f88ff",
      dark: "#4b44cc",
    },
    secondary: {
      main: "#03dac6",
    },
    background: {
      default: "#f8f9fa",
      paper: "#ffffff",
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  shape: { borderRadius: 12 },
});

export default theme;
