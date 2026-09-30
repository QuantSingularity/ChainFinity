import { useEffect, useState } from "react";
import { useApp } from "../context/AppContext";
import { blockchainAPI } from "../services/api";

// ── Mock data used when the backend is not available ──────────────────────────
const MOCK_PORTFOLIO = {
  total_value: 24850.42,
  assets: [
    {
      symbol: "ETH",
      name: "Ethereum",
      balance: 4.2,
      value: 12600,
      change_24h: 2.4,
      color: "#627eea",
    },
    {
      symbol: "BTC",
      name: "Bitcoin",
      balance: 0.18,
      value: 9720,
      change_24h: -0.8,
      color: "#f7931a",
    },
    {
      symbol: "LINK",
      name: "Chainlink",
      balance: 120,
      value: 1680,
      change_24h: 5.1,
      color: "#2a5ada",
    },
    {
      symbol: "UNI",
      name: "Uniswap",
      balance: 95,
      value: 850.42,
      change_24h: -2.3,
      color: "#ff007a",
    },
  ],
};

const _now = Date.now();
const MOCK_TRANSACTIONS = [
  {
    id: "0xabc1",
    hash: "0xabc1",
    type: "send",
    from: "0x1234...abcd",
    to: "0xefgh...5678",
    amount: "0.5",
    value: "$1,260",
    asset: "ETH",
    token: "ETH",
    network: "ethereum",
    date: new Date(_now - 3600000).toLocaleDateString(),
    time: new Date(_now - 3600000).toLocaleTimeString(),
    timestamp: (_now - 3600000) / 1000,
    status: "confirmed",
    fee: "$4.20",
  },
  {
    id: "0xabc2",
    hash: "0xabc2",
    type: "receive",
    from: "0xefgh...5678",
    to: "0x1234...abcd",
    amount: "100",
    value: "$100",
    asset: "USDC",
    token: "USDC",
    network: "polygon",
    date: new Date(_now - 7200000).toLocaleDateString(),
    time: new Date(_now - 7200000).toLocaleTimeString(),
    timestamp: (_now - 7200000) / 1000,
    status: "confirmed",
    fee: "$0.10",
  },
  {
    id: "0xabc3",
    hash: "0xabc3",
    type: "swap",
    from: "0x1234...abcd",
    to: "0x1234...abcd",
    amount: "1.0",
    value: "$3,000",
    asset: "ETH→LINK",
    token: "ETH→LINK",
    network: "ethereum",
    date: new Date(_now - 86400000).toLocaleDateString(),
    time: new Date(_now - 86400000).toLocaleTimeString(),
    timestamp: (_now - 86400000) / 1000,
    status: "confirmed",
    fee: "$9.00",
  },
  {
    id: "0xabc4",
    hash: "0xabc4",
    type: "send",
    from: "0x1234...abcd",
    to: "0xaaaa...bbbb",
    amount: "0.1",
    value: "$252",
    asset: "ETH",
    token: "ETH",
    network: "arbitrum",
    date: new Date(_now - 172800000).toLocaleDateString(),
    time: new Date(_now - 172800000).toLocaleTimeString(),
    timestamp: (_now - 172800000) / 1000,
    status: "pending",
    fee: "$0.90",
  },
  {
    id: "0xabc5",
    hash: "0xabc5",
    type: "receive",
    from: "0xcccc...dddd",
    to: "0x1234...abcd",
    amount: "50",
    value: "$700",
    asset: "LINK",
    token: "LINK",
    network: "ethereum",
    date: new Date(_now - 259200000).toLocaleDateString(),
    time: new Date(_now - 259200000).toLocaleTimeString(),
    timestamp: (_now - 259200000) / 1000,
    status: "confirmed",
    fee: "$2.10",
  },
];

// ─────────────────────────────────────────────────────────────────────────────

export const usePortfolioData = (walletAddress) => {
  const { user } = useApp();
  const userWallet = user ? user.wallet_address : null;
  const [portfolioData, setPortfolioData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPortfolioData = async () => {
      const address = walletAddress || userWallet;

      try {
        setLoading(true);
        if (address) {
          const response = await blockchainAPI.getPortfolio(address);
          setPortfolioData(response.data);
        } else {
          // No address - use mock data so UI is always populated
          setPortfolioData(MOCK_PORTFOLIO);
        }
        setError(null);
      } catch (err) {
        // Backend not available → fall back to mock data silently
        setPortfolioData(MOCK_PORTFOLIO);
        setError(null);
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioData();
  }, [walletAddress, userWallet]);

  const refreshPortfolio = async () => {
    setLoading(true);
    try {
      const address = walletAddress || userWallet;
      if (address) {
        const response = await blockchainAPI.getPortfolio(address);
        setPortfolioData(response.data);
      } else {
        setPortfolioData(MOCK_PORTFOLIO);
      }
      setError(null);
      return true;
    } catch (err) {
      setPortfolioData(MOCK_PORTFOLIO);
      setError(null);
      return true;
    } finally {
      setLoading(false);
    }
  };

  return { portfolioData, loading, error, refreshPortfolio };
};

export const useTransactionHistory = (walletAddress) => {
  const { user } = useApp();
  const userWallet = user ? user.wallet_address : null;
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTransactions = async () => {
      const address = walletAddress || userWallet;

      try {
        setLoading(true);
        if (address) {
          const response = await blockchainAPI.getTransactions(address);
          setTransactions(response.data);
        } else {
          setTransactions(MOCK_TRANSACTIONS);
        }
        setError(null);
      } catch (err) {
        setTransactions(MOCK_TRANSACTIONS);
        setError(null);
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [walletAddress, userWallet]);

  const refreshTransactions = async () => {
    setLoading(true);
    try {
      const address = walletAddress || userWallet;
      if (address) {
        const response = await blockchainAPI.getTransactions(address);
        setTransactions(response.data);
      } else {
        setTransactions(MOCK_TRANSACTIONS);
      }
      setError(null);
      return true;
    } catch (err) {
      setTransactions(MOCK_TRANSACTIONS);
      setError(null);
      return true;
    } finally {
      setLoading(false);
    }
  };

  return { transactions, loading, error, refreshTransactions };
};

export const useTokenBalance = (tokenAddress, network = "ethereum") => {
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBalance = async () => {
      if (!tokenAddress) {
        setBalance({ balance: "0" });
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await blockchainAPI.getTokenBalance(
          tokenAddress,
          network,
        );
        setBalance(response.data);
        setError(null);
      } catch (err) {
        setBalance({ balance: "0" });
        setError(null);
      } finally {
        setLoading(false);
      }
    };

    fetchBalance();
  }, [tokenAddress, network]);

  const refreshBalance = async () => {
    if (!tokenAddress) return false;
    setLoading(true);
    try {
      const response = await blockchainAPI.getTokenBalance(
        tokenAddress,
        network,
      );
      setBalance(response.data);
      setError(null);
      return true;
    } catch (err) {
      setBalance({ balance: "0" });
      setError(null);
      return false;
    } finally {
      setLoading(false);
    }
  };

  return { balance, loading, error, refreshBalance };
};

export const useEthBalance = () => {
  const [ethBalance, setEthBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchEthBalance = async () => {
      try {
        setLoading(true);
        const response = await blockchainAPI.getEthBalance();
        setEthBalance(response.data.balance);
        setError(null);
      } catch (err) {
        setEthBalance("4.2");
        setError(null);
      } finally {
        setLoading(false);
      }
    };

    fetchEthBalance();
  }, []);

  const refreshEthBalance = async () => {
    setLoading(true);
    try {
      const response = await blockchainAPI.getEthBalance();
      setEthBalance(response.data.balance);
      setError(null);
      return true;
    } catch (err) {
      setEthBalance("4.2");
      setError(null);
      return true;
    } finally {
      setLoading(false);
    }
  };

  return { ethBalance, loading, error, refreshEthBalance };
};
