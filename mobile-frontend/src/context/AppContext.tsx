"use client";

import { ethers } from "ethers";
import type React from "react";
import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { type ApiError, authAPI, handleApiError } from "../services/api";

interface User {
  id: string;
  username: string;
  email: string;
}

interface WalletState {
  isConnected: boolean;
  address: string | null;
  balance: string | null;
  network: string | null;
}

interface AppState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: ApiError | null;
  darkMode: boolean;
  wallet: WalletState;
}

interface AppActions {
  login: (credentials: any) => Promise<boolean>;
  register: (
    userData: any,
  ) => Promise<{ success: boolean; data?: any; error?: ApiError }>;
  logout: () => void;
  clearError: () => void;
  toggleTheme: () => void;
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
}

const AppContext = createContext<
  (AppState & { actions: AppActions }) | undefined
>(undefined);

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

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, setState] = useState<AppState>(initialState);
  // Use a ref so connectWallet can call disconnectWallet without circular deps
  const disconnectWalletRef = useRef<() => void>(() => {});

  useEffect(() => {
    const initApp = async () => {
      let initialDarkMode = false;
      let initialUser: User | null = null;
      let initialIsAuthenticated = false;

      if (typeof window !== "undefined") {
        initialDarkMode = localStorage.getItem("darkMode") === "true";
        const token = localStorage.getItem("token");
        const storedUser = localStorage.getItem("user");

        if (token && storedUser) {
          try {
            initialUser = JSON.parse(storedUser);
            initialIsAuthenticated = true;
          } catch (_err) {
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            initialUser = null;
            initialIsAuthenticated = false;
          }
        }
      }

      setState((prev) => ({
        ...prev,
        darkMode: initialDarkMode,
        user: initialUser,
        isAuthenticated: initialIsAuthenticated,
        loading: false,
      }));
    };
    initApp();
  }, []);

  const toggleTheme = useCallback(() => {
    setState((prev) => {
      const newMode = !prev.darkMode;
      if (typeof window !== "undefined") {
        localStorage.setItem("darkMode", String(newMode));
        document.documentElement.classList.toggle("dark", newMode);
      }
      return { ...prev, darkMode: newMode };
    });
  }, []);

  const login = useCallback(async (credentials: any): Promise<boolean> => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const response = await authAPI.login(credentials);
      const { access_token } = response.data;
      localStorage.setItem("token", access_token);

      const userResponse = await authAPI.getCurrentUser();
      const loggedInUser = userResponse.data;
      localStorage.setItem("user", JSON.stringify(loggedInUser));

      setState((prev) => ({
        ...prev,
        user: loggedInUser,
        isAuthenticated: true,
        loading: false,
      }));
      return true;
    } catch (err) {
      const apiError = handleApiError(err);
      setState((prev) => ({ ...prev, error: apiError, loading: false }));
      return false;
    }
  }, []);

  const register = useCallback(
    async (
      userData: any,
    ): Promise<{ success: boolean; data?: any; error?: ApiError }> => {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const response = await authAPI.register(userData);
        setState((prev) => ({ ...prev, loading: false }));
        return { success: true, data: response.data };
      } catch (err) {
        const apiError = handleApiError(err);
        setState((prev) => ({ ...prev, error: apiError, loading: false }));
        return { success: false, error: apiError };
      }
    },
    [],
  );

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setState((prev) => ({ ...prev, user: null, isAuthenticated: false }));
  }, []);

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  const disconnectWallet = useCallback(() => {
    if (
      typeof window !== "undefined" &&
      typeof window.ethereum?.removeListener === "function"
    ) {
      window.ethereum.removeListener("accountsChanged", () => {});
      window.ethereum.removeListener("chainChanged", () => {});
    }
    setState((prev) => ({ ...prev, wallet: initialWalletState }));
  }, []);

  // Keep ref in sync so connectWallet can call it without stale closure
  disconnectWalletRef.current = disconnectWallet;

  const connectWallet = useCallback(async () => {
    if (
      typeof window === "undefined" ||
      typeof window.ethereum === "undefined"
    ) {
      setState((prev) => ({
        ...prev,
        error: {
          message: "Wallet not detected. Please install MetaMask.",
          status: 404,
        },
      }));
      return;
    }
    try {
      const accounts = await window.ethereum.request({
        method: "eth_requestAccounts",
      });
      const address = accounts[0];
      const provider = new ethers.BrowserProvider(window.ethereum);
      const balanceWei = await provider.getBalance(address);
      const balanceEth = ethers.formatEther(balanceWei);
      const network = await provider.getNetwork();
      const networkName =
        network.name === "homestead" ? "Ethereum Mainnet" : network.name;

      setState((prev) => ({
        ...prev,
        wallet: {
          isConnected: true,
          address,
          balance: `${parseFloat(balanceEth).toFixed(4)} ETH`,
          network: networkName,
        },
      }));

      const handleAccountsChanged = (newAccounts: string[]) => {
        if (newAccounts.length === 0) {
          disconnectWalletRef.current();
        } else {
          connectWallet();
        }
      };

      const handleChainChanged = () => {
        window.location.reload();
      };

      window.ethereum.removeListener("accountsChanged", handleAccountsChanged);
      window.ethereum.removeListener("chainChanged", handleChainChanged);
      window.ethereum.on("accountsChanged", handleAccountsChanged);
      window.ethereum.on("chainChanged", handleChainChanged);
    } catch (error) {
      console.error("Failed to connect wallet:", error);
      setState((prev) => ({
        ...prev,
        error: {
          message: "Failed to connect wallet. Please try again.",
          status: 500,
        },
      }));
    }
  }, []);

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

export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
};

export default AppContext;
