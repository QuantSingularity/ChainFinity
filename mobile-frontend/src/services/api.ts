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

export interface PortfolioSummary {
  id: string;
  name: string;
}

export interface VolatilityForecast {
  symbol?: string | null;
  predicted_vol: number;
  predicted_vol_std: number | null;
  confidence_interval: number[] | null;
  vol_bucket: "low" | "medium" | "high" | "extreme";
  confidence: number | null;
  recent_realized_vol: number;
  forecast_horizon_days: number;
  model: string;
}

export interface CorrelationResult {
  assets: string[];
  matrix: number[][];
  model: string;
}

export interface PortfolioAIInsights {
  portfolio_id: string;
  generated_at: string;
  assets: string[];
  correlation: CorrelationResult | null;
  volatility: Record<string, VolatilityForecast>;
  warnings: string[];
}

export interface StressTestResult {
  scenario_name: string;
  status: string;
  potential_loss_percent?: number;
}

export interface RiskAssessment {
  id: string;
  risk_score: number | string;
  risk_level: string;
  risk_grade?: string | null;
  action_required: boolean;
  recommendations: string[];
  stress_tests: StressTestResult[];
}

export interface AIModelStatus {
  loaded: boolean;
  mode: string;
  fallback: string | null;
}

export interface AIStatus {
  enabled: boolean;
  package_available: boolean;
  tensorflow_available: boolean;
  models: Record<string, AIModelStatus>;
}

export const portfolioAPI = {
  list: (page = 1, size = 20) =>
    api.get("/api/v1/portfolios/", { params: { page, size } }),
};

export const riskAPI = {
  assess: (portfolioId: string) =>
    api.post(`/api/v1/risk/assess/${portfolioId}`),
  getMetrics: (portfolioId: string) =>
    api.get(`/api/v1/risk/metrics/${portfolioId}`),
  monitor: (portfolioId: string) =>
    api.get(`/api/v1/risk/monitor/${portfolioId}`),
  stressTest: (portfolioId: string, scenario = "Market Crash") =>
    api.post(`/api/v1/risk/stress-test/${portfolioId}`, null, {
      params: { scenario },
    }),
  listAssessments: (params: Record<string, unknown> = {}) =>
    api.get("/api/v1/risk/assessments", { params }),
};

export const aiAPI = {
  getStatus: () => api.get("/api/v1/ai/status"),
  forecastVolatility: (payload: Record<string, unknown>) =>
    api.post("/api/v1/ai/volatility", payload),
  predictCorrelation: (payload: Record<string, unknown>) =>
    api.post("/api/v1/ai/correlation", payload),
  detectExploits: (payload: Record<string, unknown>) =>
    api.post("/api/v1/ai/exploit-detection", payload),
  assessLiquidity: (payload: Record<string, unknown>) =>
    api.post("/api/v1/ai/liquidity", payload),
  analyzeSmartMoney: (payload: Record<string, unknown>) =>
    api.post("/api/v1/ai/smart-money", payload),
  getPortfolioInsights: (portfolioId: string, horizonDays = 7) =>
    api.get(`/api/v1/ai/portfolio/${portfolioId}/insights`, {
      params: { horizon_days: horizonDays },
    }),
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
