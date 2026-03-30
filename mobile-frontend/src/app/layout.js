"use client";

import { Box } from "@mui/material";
import Footer from "../components/layout/Footer"; // Adjusted path
import Navbar from "../components/layout/Navbar"; // Adjusted path
import { AppProvider } from "../context/AppContext"; // Adjusted path
import ThemeRegistry from "../ThemeRegistry"; // Adjusted path

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <ThemeRegistry>
          <AppProvider>
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                minHeight: "100vh",
              }}
            >
              <Navbar />
              <Box component="main" sx={{ flexGrow: 1, pt: { xs: 7, sm: 8 } }}>
                {" "}
                {/* Add padding top for fixed Navbar */}
                {children}
              </Box>
              <Footer />
            </Box>
          </AppProvider>
        </ThemeRegistry>
      </body>
    </html>
  );
}
