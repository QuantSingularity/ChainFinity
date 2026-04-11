import { useEffect, useState } from "react";
import { useApp } from "../context/AppContext";
import { blockchainAPI, handleApiError } from "../services/api";

export const usePortfolioData = (walletAddress) => {
  const { user } = useApp();
  const [portfolioData, setPortfolioData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const resolvedAddress = walletAddress || user?.wallet_address || null;

  useEffect(() => {
    const fetchPortfolioData = async () => {
      if (!resolvedAddress) {
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const response = await blockchainAPI.getPortfolio(resolvedAddress);
        setPortfolioData(response.data);
        setError(null);
      } catch (err) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };
    fetchPortfolioData();
  }, [resolvedAddress]);

  const refreshPortfolio = async () => {
    if (!resolvedAddress) return false;
    setLoading(true);
    try {
      const response = await blockchainAPI.getPortfolio(resolvedAddress);
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

  const resolvedAddress = walletAddress || user?.wallet_address || null;

  useEffect(() => {
    const fetchTransactions = async () => {
      if (!resolvedAddress) {
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const response = await blockchainAPI.getTransactions(resolvedAddress);
        setTransactions(response.data);
        setError(null);
      } catch (err) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };
    fetchTransactions();
  }, [resolvedAddress]);

  const refreshTransactions = async () => {
    if (!resolvedAddress) return false;
    setLoading(true);
    try {
      const response = await blockchainAPI.getTransactions(resolvedAddress);
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
