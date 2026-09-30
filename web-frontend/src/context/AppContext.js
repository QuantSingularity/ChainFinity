import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { authAPI, handleApiError } from "../services/api";

// Normalize the backend user shape to what the UI consumes. The backend's
// UserResponse exposes `primary_wallet_address` and has no display `name`,
// while the UI reads `wallet_address` and `name`. Map between them here so
// either shape works.
const normalizeUser = (raw) => {
  if (!raw) return raw;
  const walletAddress =
    raw.wallet_address ?? raw.primary_wallet_address ?? null;
  const name =
    raw.name ||
    [raw.first_name, raw.last_name].filter(Boolean).join(" ") ||
    (raw.email ? raw.email.split("@")[0] : undefined);
  return { ...raw, wallet_address: walletAddress, name };
};

// Create context
const AppContext = createContext();

// Provider component
export const AppProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [darkMode, setDarkMode] = useState(
    localStorage.getItem("darkMode") === "true",
  );

  // Logout function - defined before useEffect with useCallback to stabilize reference
  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  // Initialize auth state from localStorage on app load
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem("token");
      const storedUser = localStorage.getItem("user");

      if (token && storedUser) {
        try {
          const parsed = JSON.parse(storedUser);
          setUser(parsed);
          setIsAuthenticated(true);

          // Attempt to verify token with backend (optional - fails gracefully)
          try {
            const response = await authAPI.getCurrentUser();
            const verifiedUser = normalizeUser(response.data);
            setUser(verifiedUser);
            localStorage.setItem("user", JSON.stringify(verifiedUser));
          } catch (_verifyErr) {
            // Backend unreachable or token expired - keep cached user for now
            // Only force logout on explicit 401 (invalid token)
            if (_verifyErr?.response?.status === 401) {
              logout();
            }
          }
        } catch (err) {
          // Corrupted localStorage data
          logout();
        }
      }

      setLoading(false);
    };

    initAuth();
  }, [logout]);

  // Toggle dark mode
  const toggleTheme = () => {
    setDarkMode((prev) => {
      const next = !prev;
      localStorage.setItem("darkMode", next);
      return next;
    });
  };

  // Login function
  const login = async (credentials) => {
    setLoading(true);
    setError(null);

    // Demo mode: allow guest login without backend
    const isDemo =
      credentials.email === "guest@chainfinity.io" ||
      credentials.email === "demo@chainfinity.io";

    if (isDemo) {
      const demoUser = {
        id: "demo-user",
        name: "Demo User",
        email: credentials.email,
        wallet_address: "0xDEMO1234567890abcdef1234567890abcdef1234",
      };
      localStorage.setItem("token", "demo-token");
      localStorage.setItem("user", JSON.stringify(demoUser));
      setUser(demoUser);
      setIsAuthenticated(true);
      setLoading(false);
      return true;
    }

    try {
      const response = await authAPI.login(credentials);
      const { access_token } = response.data;

      // Store token
      localStorage.setItem("token", access_token);

      // Get user data
      const userResponse = await authAPI.getCurrentUser();
      const loggedInUser = normalizeUser(userResponse.data);
      setUser(loggedInUser);
      localStorage.setItem("user", JSON.stringify(loggedInUser));

      setIsAuthenticated(true);
      setLoading(false);
      return true;
    } catch (err) {
      setError(handleApiError(err));
      setLoading(false);
      return false;
    }
  };

  // Register function
  const register = async (userData) => {
    setLoading(true);
    setError(null);

    try {
      const response = await authAPI.register(userData);
      setLoading(false);
      return { success: true, data: response.data };
    } catch (err) {
      const apiError = handleApiError(err);
      setError(apiError);
      setLoading(false);
      return { success: false, error: apiError };
    }
  };

  // Clear error
  const clearError = () => {
    setError(null);
  };

  // Context value
  const value = {
    user,
    isAuthenticated,
    loading,
    error,
    darkMode,
    login,
    register,
    logout,
    clearError,
    toggleTheme,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Custom hook to use the auth context
export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
};

export default AppContext;
