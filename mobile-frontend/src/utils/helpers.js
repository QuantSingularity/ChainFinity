import { ethers } from "ethers";

export const formatAddress = (address) => {
  if (!address) return "";
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
};

export const formatTokenAmount = (amount, decimals = 18) => {
  try {
    return ethers.formatUnits(amount, decimals);
  } catch (error) {
    console.error("Error formatting token amount:", error);
    return "0";
  }
};

export const formatDate = (timestamp) => {
  const date = new Date(timestamp * 1000);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const isValidAddress = (address) => {
  try {
    return ethers.isAddress(address);
  } catch (_error) {
    return false;
  }
};

export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error("Error copying to clipboard:", error);
    return false;
  }
};

export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

export const formatLargeNumber = (num) => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
  return num.toString();
};

export const generateId = () => Math.random().toString(36).substr(2, 9);

export const isEmpty = (obj) => Object.keys(obj).length === 0;

export const deepClone = (obj) => JSON.parse(JSON.stringify(obj));
