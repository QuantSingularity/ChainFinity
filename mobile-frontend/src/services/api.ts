import axios, { type AxiosError } from "axios";

// API Error type
export interface ApiError {
  status: number;
  message: string;
}

// Create an axios instance with default config
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Add a request interceptor to include auth token in requests
api.interceptors.request.use(
  (config) => {
    // Only access localStorage on client side
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Add a response interceptor to handle common errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Handle 401 Unauthorized errors (token expired or invalid)
    if (error.response && error.response.status === 401) {
      // Clear local storage and redirect to login (only on client side)
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

// Auth API endpoints
export const authAPI = {
  register: (userData: any) => api.post("/api/v1/auth/register", userData),
  login: (credentials: any) => api.post("/api/v1/auth/token", credentials),
  getCurrentUser: () => api.get("/api/v1/auth/me"),
  updatePassword: (data: { currentPassword: string; newPassword: string }) =>
    api.put("/api/v1/auth/password", data),
  updateProfile: (data: any) => api.put("/api/v1/auth/me", data),
};

// Blockchain API endpoints
export const blockchainAPI = {
  getPortfolio: (walletAddress: string) =>
    api.get(`/api/v1/blockchain/portfolio/${walletAddress}`),
  getTransactions: (walletAddress: string) =>
    api.get(`/api/v1/blockchain/transactions/${walletAddress}`),
  getTokenBalance: (tokenAddress: string, network: string = "ethereum") =>
    api.get(`/api/v1/blockchain/balance/${tokenAddress}?network=${network}`),
  getEthBalance: () => api.get("/api/v1/blockchain/eth-balance"),
};

// Portfolios API endpoints
export const portfoliosAPI = {
  list: () => api.get("/api/v1/portfolios"),
  get: (id: string) => api.get(`/api/v1/portfolios/${id}`),
  create: (data: any) => api.post("/api/v1/portfolios", data),
  update: (id: string, data: any) => api.put(`/api/v1/portfolios/${id}`, data),
  delete: (id: string) => api.delete(`/api/v1/portfolios/${id}`),
};

// Transactions API endpoints
export const transactionsAPI = {
  list: (params?: any) => api.get("/api/v1/transactions", { params }),
  get: (id: string) => api.get(`/api/v1/transactions/${id}`),
};

// Risk API endpoints
export const riskAPI = {
  assess: (data: any) => api.post("/api/v1/risk/assess", data),
  getRiskMetrics: (portfolioId: string) =>
    api.get(`/api/v1/risk/metrics/${portfolioId}`),
};

// Helper function to handle API errors
export const handleApiError = (error: any): ApiError => {
  if (error.response) {
    // The request was made and the server responded with a status code
    // that falls out of the range of 2xx
    const { status, data } = error.response;
    return {
      status,
      message: data.detail || data.message || "An error occurred",
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
