import { Box, CircularProgress, CssBaseline } from "@mui/material";
import { Navigate, Route, Routes } from "react-router-dom";
import Footer from "./components/layout/Footer";
import Navbar from "./components/layout/Navbar";
import { useApp } from "./context/AppContext";
import Dashboard from "./pages/Dashboard";
import ForgotPassword from "./pages/ForgotPassword";
import GovernancePage from "./pages/Governance/index";
import GovernanceAnalyticsPage from "./pages/Governance/Analytics";
import Home from "./pages/Home";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import PortfolioPage from "./pages/PortfolioPage";
import Register from "./pages/Register";
import RiskInsights from "./pages/RiskInsights";
import Settings from "./pages/Settings";
import Transactions from "./pages/Transactions";

function App() {
  const { isAuthenticated, loading } = useApp();

  // Wait for auth state to resolve before rendering routes - prevents
  // redirect flicker and ensures the correct page is shown on first load.
  if (loading) {
    return (
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100vh",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Redirect authenticated users away from auth/marketing pages to dashboard.
  const PublicRoute = ({ element }) =>
    isAuthenticated ? <Navigate to="/dashboard" replace /> : element;

  // Redirect unauthenticated users to login.
  const ProtectedRoute = ({ element }) =>
    isAuthenticated ? element : <Navigate to="/login" replace />;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <CssBaseline />
      <Navbar />
      <Box component="main" sx={{ flexGrow: 1 }}>
        <Routes>
          {/* Public routes - redirect to /dashboard if already logged in */}
          <Route path="/" element={<PublicRoute element={<Home />} />} />
          <Route path="/login" element={<PublicRoute element={<Login />} />} />
          <Route
            path="/register"
            element={<PublicRoute element={<Register />} />}
          />
          <Route path="/forgot-password" element={<ForgotPassword />} />

          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={<ProtectedRoute element={<Dashboard />} />}
          />
          <Route
            path="/portfolio"
            element={<ProtectedRoute element={<PortfolioPage />} />}
          />
          <Route
            path="/risk"
            element={<ProtectedRoute element={<RiskInsights />} />}
          />
          <Route
            path="/transactions"
            element={<ProtectedRoute element={<Transactions />} />}
          />
          <Route
            path="/governance"
            element={<ProtectedRoute element={<GovernancePage />} />}
          />
          <Route
            path="/governance/analytics"
            element={<ProtectedRoute element={<GovernanceAnalyticsPage />} />}
          />
          <Route
            path="/settings"
            element={<ProtectedRoute element={<Settings />} />}
          />

          {/* Catch-all */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Box>
      <Footer />
    </Box>
  );
}

export default App;
