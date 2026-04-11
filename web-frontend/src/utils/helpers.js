// Format Ethereum address
export const formatAddress = (address) => {
  if (!address) return "";
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
};

// Format token amount (ethers v6 compatible)
export const formatTokenAmount = (amount, decimals = 18) => {
  try {
    // Handle BigInt or string amounts without ethers dependency
    const num = typeof amount === "bigint" ? amount : BigInt(amount);
    const divisor = BigInt(10) ** BigInt(decimals);
    const whole = num / divisor;
    const fraction = num % divisor;
    const fractionStr = fraction.toString().padStart(decimals, "0").slice(0, 6);
    return `${whole}.${fractionStr}`.replace(/\.?0+$/, "");
  } catch (error) {
    console.error("Error formatting token amount:", error);
    return "0";
  }
};

// Format date
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

// Validate Ethereum address
export const isValidAddress = (address) => {
  if (!address) return false;
  return /^0x[0-9a-fA-F]{40}$/.test(address);
};

// Copy to clipboard
export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error("Error copying to clipboard:", error);
    return false;
  }
};

// Debounce function
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

// Format large numbers
export const formatLargeNumber = (num) => {
  const n = Number(num);
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(2)}K`;
  return n.toString();
};

// Format currency value
export const formatCurrency = (value, currency = "USD") => {
  const num = Number(value);
  if (isNaN(num)) return "$0.00";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
};

// Generate random ID
export const generateId = () => {
  return Math.random().toString(36).substring(2, 11);
};

// Check if object is empty
export const isEmpty = (obj) => {
  return obj == null || Object.keys(obj).length === 0;
};

// Deep clone object
export const deepClone = (obj) => {
  return JSON.parse(JSON.stringify(obj));
};

// Truncate text
export const truncateText = (text, maxLength = 50) => {
  if (!text || text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}...`;
};

// Calculate percentage change
export const calcPercentChange = (current, previous) => {
  if (!previous || previous === 0) return 0;
  return ((current - previous) / previous) * 100;
};
