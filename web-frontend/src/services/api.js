import axios from "axios";

// Base URL of the backend, e.g. http://localhost:8000. All endpoint paths
// below include the backend's versioned prefix (/api/v1/...). The previous
// version hit /api/auth/token and /api/blockchain/... — neither of which the
// backend serves (it exposes /api/v1/auth/login, /api/v1/auth/me, and
// /api/v1/blockchain/...), so every real request 404'd and the app only
// appeared to work via its demo-mode and mock-data fallbacks.
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Create an axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add a request interceptor to include auth token in requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Add a response interceptor to handle common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized errors (token expired or invalid)
    if (error.response && error.response.status === 401) {
      // Clear local storage and redirect to login
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

// Auth API endpoints (backend: /api/v1/auth/*)
export const authAPI = {
  register: (userData) => api.post("/api/v1/auth/register", userData),
  login: (credentials) => api.post("/api/v1/auth/login", credentials),
  getCurrentUser: () => api.get("/api/v1/auth/me"),
};

// Blockchain API endpoints (backend: /api/v1/blockchain/*)
export const blockchainAPI = {
  getPortfolio: (walletAddress) =>
    api.get(`/api/v1/blockchain/portfolio/${walletAddress}`),
  getTransactions: (walletAddress) =>
    api.get(`/api/v1/blockchain/transactions/${walletAddress}`),
  getTokenBalance: (tokenAddress, network = "ethereum") =>
    api.get(`/api/v1/blockchain/balance/${tokenAddress}?network=${network}`),
  getEthBalance: () => api.get("/api/v1/blockchain/eth-balance"),
  getGasPrice: (network = "ethereum") =>
    api.get(`/api/v1/blockchain/gas-price?network=${network}`),
  verifyAddress: (address, network = "ethereum") =>
    api.post(
      `/api/v1/blockchain/verify-address?address=${encodeURIComponent(address)}&network=${network}`,
    ),
  // ChainFinity's own deployed contract addresses (AssetVault,
  // CrossChainManager, InstitutionalDeFiProtocol, GovernanceToken,
  // InstitutionalGovernance) for the network the backend is connected to.
  // This is how the frontend learns what to call instead of hardcoding
  // addresses at build time - see services/blockchain/web3_client.py.
  getDeployedContracts: () => api.get("/api/v1/blockchain/deployed-contracts"),
};

// Helper function to handle API errors
export const handleApiError = (error) => {
  if (error.response) {
    // The request was made and the server responded with a status code
    // that falls out of the range of 2xx
    const { status, data } = error.response;
    return {
      status,
      message: data.detail || "An error occurred",
    };
  } else if (error.request) {
    // The request was made but no response was received
    return {
      status: 0,
      message: "No response from server. Please check your connection.",
    };
  } else {
    // Something happened in setting up the request that triggered an Error
    return {
      status: 0,
      message: error.message || "An unknown error occurred",
    };
  }
};

export default api;
