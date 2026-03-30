import { useEffect, useState } from "react";
import { useApp } from "../context/AppContext";
import { blockchainAPI, handleApiError } from "../services/api";

export const usePortfolioData = (walletAddress) => {
  const { user } = useApp();
  const [portfolioData, setPortfolioData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPortfolioData = async () => {
      if (!walletAddress && user) {
        walletAddress = user.wallet_address;
      }

      if (!walletAddress) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await blockchainAPI.getPortfolio(walletAddress);
        setPortfolioData(response.data);
        setError(null);
      } catch (err) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioData();
  }, [walletAddress, user]);

  const refreshPortfolio = async () => {
    setLoading(true);
    try {
      const address = walletAddress || (user ? user.wallet_address : null);
      if (!address) {
        throw new Error("No wallet address available");
      }

      const response = await blockchainAPI.getPortfolio(address);
      setPortfolioData(response.data);
      setError(null);
      return true;
    } catch (err) {
      setError(handleApiError(err));
      return false;
    } finally {
      setLoading(false);
    }
  };

  return { portfolioData, loading, error, refreshPortfolio };
};

export const useTransactionHistory = (walletAddress) => {
  const { user } = useApp();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTransactions = async () => {
      if (!walletAddress && user) {
        walletAddress = user.wallet_address;
      }

      if (!walletAddress) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await blockchainAPI.getTransactions(walletAddress);
        setTransactions(response.data);
        setError(null);
      } catch (err) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [walletAddress, user]);

  const refreshTransactions = async () => {
    setLoading(true);
    try {
      const address = walletAddress || (user ? user.wallet_address : null);
      if (!address) {
        throw new Error("No wallet address available");
      }

      const response = await blockchainAPI.getTransactions(address);
      setTransactions(response.data);
      setError(null);
      return true;
    } catch (err) {
      setError(handleApiError(err));
      return false;
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
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };

    fetchBalance();
  }, [tokenAddress, network]);

  const refreshBalance = async () => {
    if (!tokenAddress) {
      return false;
    }

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
      setError(handleApiError(err));
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
        setError(handleApiError(err));
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
      setError(handleApiError(err));
      return false;
    } finally {
      setLoading(false);
    }
  };

  return { ethBalance, loading, error, refreshEthBalance };
};
