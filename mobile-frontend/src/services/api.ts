import AsyncStorage from "@react-native-async-storage/async-storage";
import axios, { AxiosError } from "axios";

// Base URL of the backend. Expo exposes EXPO_PUBLIC_* variables to the app.
// All endpoint paths include the backend's versioned prefix (/api/v1/...),
// matching the FastAPI routes (auth/login, auth/me, blockchain/...).
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

export const TOKEN_KEY = "chainfinity.token";
export const USER_KEY = "chainfinity.user";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

// Attach the bearer token from AsyncStorage to every request.
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear stored credentials. Navigation back to the login screen is
// handled by the auth context observing the cleared state (a mobile app has
// no window.location to redirect).
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response && error.response.status === 401) {
      await AsyncStorage.multiRemove([TOKEN_KEY, USER_KEY]);
    }
    return Promise.reject(error);
  },
);

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  confirm_password: string;
  terms_accepted: boolean;
  privacy_accepted: boolean;
  wallet_address?: string;
}

// Auth API endpoints (backend: /api/v1/auth/*)
export const authAPI = {
  register: (userData: RegisterData) =>
    api.post("/api/v1/auth/register", userData),
  login: (credentials: LoginCredentials) =>
    api.post("/api/v1/auth/login", credentials),
  getCurrentUser: () => api.get("/api/v1/auth/me"),
};

// Blockchain API endpoints (backend: /api/v1/blockchain/*)
export const blockchainAPI = {
  getPortfolio: (walletAddress: string) =>
    api.get(`/api/v1/blockchain/portfolio/${walletAddress}`),
  getTransactions: (walletAddress: string) =>
    api.get(`/api/v1/blockchain/transactions/${walletAddress}`),
  getTokenBalance: (tokenAddress: string, network = "ethereum") =>
    api.get(`/api/v1/blockchain/balance/${tokenAddress}?network=${network}`),
  getEthBalance: () => api.get("/api/v1/blockchain/eth-balance"),
  getGasPrice: (network = "ethereum") =>
    api.get(`/api/v1/blockchain/gas-price?network=${network}`),
  verifyAddress: (address: string, network = "ethereum") =>
    api.post(
      `/api/v1/blockchain/verify-address?address=${encodeURIComponent(address)}&network=${network}`,
    ),
  // ChainFinity's own deployed contract addresses for the network the
  // backend is connected to - see services/blockchain/web3_client.py.
  getDeployedContracts: () => api.get("/api/v1/blockchain/deployed-contracts"),
};

export interface ApiErrorInfo {
  status: number;
  message: string;
}

// Normalise axios errors into a UI-friendly shape.
export const handleApiError = (error: unknown): ApiErrorInfo => {
  const err = error as AxiosError<{ detail?: string }>;
  if (err?.response) {
    return {
      status: err.response.status,
      message: err.response.data?.detail || "An error occurred",
    };
  }
  if (err?.request) {
    return {
      status: 0,
      message: "No response from server. Please check your connection.",
    };
  }
  return {
    status: 0,
    message: (err as Error)?.message || "An unknown error occurred",
  };
};

export default api;
