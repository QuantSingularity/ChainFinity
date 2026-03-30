// src/context/AppContext.tsx

import { ethers } from "ethers"; // Import ethers for balance formatting
import type React from "react";
import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { type ApiError, authAPI, handleApiError } from "../services/api"; // Assuming these exist and are typed

// Define types for context state
interface User {
  id: string;
  username: string;
  email: string;
  // Add other user properties as needed
}

interface WalletState {
  isConnected: boolean;
  address: string | null;
  balance: string | null; // Store balance as formatted string
  network: string | null; // Store network name or chain ID
  // Add recent transactions if needed later
}

interface AppState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: ApiError | null;
  darkMode: boolean;
  wallet: WalletState;
}

// Define types for context actions
interface AppActions {
  login: (credentials: any) => Promise<boolean>; // Replace 'any' with specific credentials type
  register: (
    userData: any,
  ) => Promise<{ success: boolean; data?: any; error?: ApiError }>; // Replace 'any' with specific user data type
  logout: () => void;
  clearError: () => void;
  toggleTheme: () => void;
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
}

// Create context with initial state and undefined actions (will be provided by provider)
const AppContext = createContext<
  (AppState & { actions: AppActions }) | undefined
>(undefined);

// Initial state values
const initialWalletState: WalletState = {
  isConnected: false,
  address: null,
  balance: null,
  network: null,
};

const initialState: AppState = {
  user: null,
  isAuthenticated: false,
  loading: true,
  error: null,
  darkMode: false,
  wallet: initialWalletState,
};

// Provider component
interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, setState] = useState<AppState>(initialState);

  // Initialize auth state and theme from localStorage on app load
  useEffect(() => {
    const initApp = async () => {
      let initialDarkMode = false;
      let initialUser: User | null = null;
      let initialIsAuthenticated = false;
      const _initialLoading = true;

      if (typeof window !== "undefined") {
        initialDarkMode = localStorage.getItem("darkMode") === "true";
        const token = localStorage.getItem("token");
        const storedUser = localStorage.getItem("user");

        if (token && storedUser) {
          try {
            initialUser = JSON.parse(storedUser);
            initialIsAuthenticated = true;
            // Verify token (optional but recommended)
            // const response = await authAPI.getCurrentUser();
            // initialUser = response.data;
          } catch (_err) {
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            initialUser = null;
            initialIsAuthenticated = false;
          }
        }
      }

      setState((prevState) => ({
        ...prevState,
        darkMode: initialDarkMode,
        user: initialUser,
        isAuthenticated: initialIsAuthenticated,
        loading: false, // Set loading false after initialization
      }));
    };

    initApp();
  }, []);

  // Toggle dark mode
  const toggleTheme = useCallback(() => {
    setState((prevState) => {
      const newMode = !prevState.darkMode;
      if (typeof window !== "undefined") {
        localStorage.setItem("darkMode", String(newMode));
        document.documentElement.classList.toggle("dark", newMode);
      }
      return { ...prevState, darkMode: newMode };
    });
  }, []);

  // Login function
  const login = useCallback(async (credentials: any): Promise<boolean> => {
    setState((prevState) => ({ ...prevState, loading: true, error: null }));
    try {
      const response = await authAPI.login(credentials);
      const { access_token } = response.data;
      localStorage.setItem("token", access_token);

      const userResponse = await authAPI.getCurrentUser();
      const loggedInUser = userResponse.data;
      localStorage.setItem("user", JSON.stringify(loggedInUser));

      setState((prevState) => ({
        ...prevState,
        user: loggedInUser,
        isAuthenticated: true,
        loading: false,
      }));
      return true;
    } catch (err) {
      const apiError = handleApiError(err);
      setState((prevState) => ({
        ...prevState,
        error: apiError,
        loading: false,
      }));
      return false;
    }
  }, []);

  // Register function
  const register = useCallback(
    async (
      userData: any,
    ): Promise<{ success: boolean; data?: any; error?: ApiError }> => {
      setState((prevState) => ({ ...prevState, loading: true, error: null }));
      try {
        const response = await authAPI.register(userData);
        setState((prevState) => ({ ...prevState, loading: false }));
        return { success: true, data: response.data };
      } catch (err) {
        const apiError = handleApiError(err);
        setState((prevState) => ({
          ...prevState,
          error: apiError,
          loading: false,
        }));
        return { success: false, error: apiError };
      }
    },
    [],
  );

  // Logout function
  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setState((prevState) => ({
      ...prevState,
      user: null,
      isAuthenticated: false,
    }));
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setState((prevState) => ({ ...prevState, error: null }));
  }, []);

  // --- Wallet Functions ---
  const connectWallet = useCallback(async () => {
    if (typeof window.ethereum !== "undefined") {
      try {
        // Request account access
        const accounts = await window.ethereum.request({
          method: "eth_requestAccounts",
        });
        const address = accounts[0];

        // Get provider
        const provider = new ethers.BrowserProvider(window.ethereum);

        // Get balance
        const balanceWei = await provider.getBalance(address);
        const balanceEth = ethers.formatEther(balanceWei);

        // Get network info
        const network = await provider.getNetwork();
        const networkName =
          network.name === "homestead" ? "Ethereum Mainnet" : network.name;

        setState((prevState) => ({
          ...prevState,
          wallet: {
            isConnected: true,
            address: address,
            balance: `${parseFloat(balanceEth).toFixed(4)} ETH`, // Format balance
            network: networkName,
          },
        }));

        // Listen for account changes
        window.ethereum.on("accountsChanged", (newAccounts: string[]) => {
          if (newAccounts.length === 0) {
            // Handle disconnection
            disconnectWallet();
          } else {
            // Handle account switch - re-fetch data
            connectWallet(); // Reconnect essentially
          }
        });

        // Listen for network changes
        window.ethereum.on("chainChanged", (_chainId: string) => {
          // Reload or re-fetch data on network change
          window.location.reload(); // Simple approach: reload page
          // Or: connectWallet(); // Re-fetch data for new network
        });
      } catch (error) {
        console.error("Failed to connect wallet:", error);
        setState((prevState) => ({
          ...prevState,
          error: {
            message: "Failed to connect wallet. Please try again.",
            status: 500,
          },
        }));
      }
    } else {
      console.error("MetaMask (or other Ethereum wallet) not detected.");
      setState((prevState) => ({
        ...prevState,
        error: {
          message: "Wallet not detected. Please install MetaMask.",
          status: 404,
        },
      }));
      // Optionally prompt user to install MetaMask
    }
  }, [
    // Handle disconnection
    disconnectWallet,
  ]);

  const disconnectWallet = useCallback(() => {
    // Remove listeners if added
    if (typeof window.ethereum?.removeListener === "function") {
      window.ethereum.removeListener("accountsChanged", connectWallet); // Use the same handler reference if possible
      window.ethereum.removeListener("chainChanged", () =>
        window.location.reload(),
      );
    }
    setState((prevState) => ({
      ...prevState,
      wallet: initialWalletState, // Reset wallet state
    }));
    // Note: This doesn't fully disconnect from MetaMask, just clears app state.
    // User needs to disconnect manually in MetaMask extension.
  }, [connectWallet]); // Add connectWallet as dependency if used in listener removal

  // Context value combining state and actions
  const value = {
    ...state,
    actions: {
      login,
      register,
      logout,
      clearError,
      toggleTheme,
      connectWallet,
      disconnectWallet,
    },
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Custom hook to use the app context
export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
};

export default AppContext;
