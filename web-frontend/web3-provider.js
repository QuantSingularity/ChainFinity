import { Web3ReactProvider } from "@web3-react/core";
import { BrowserProvider } from "ethers";
import { useEffect, useState } from "react";

// Configuration
const POLLING_INTERVAL = 15000;
const _NETWORK_TIMEOUT = 10000;

export function getLibrary(provider) {
  try {
    const library = new BrowserProvider(provider);
    library.pollingInterval = POLLING_INTERVAL;
    return library;
  } catch (error) {
    console.error("Error initializing Web3Provider:", error);
    throw new Error("Failed to initialize Web3Provider");
  }
}

export function Web3Wrapper({ children }) {
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleNetworkError = (error) => {
      console.error("Web3 network error:", error);
      setError(
        "Network connection error. Please check your internet connection and try again.",
      );
    };

    window.ethereum?.on("networkChanged", handleNetworkError);
    window.ethereum?.on("accountsChanged", handleNetworkError);

    return () => {
      window.ethereum?.removeListener("networkChanged", handleNetworkError);
      window.ethereum?.removeListener("accountsChanged", handleNetworkError);
    };
  }, []);

  if (error) {
    return (
      <div style={{ padding: "20px", textAlign: "center" }}>
        <h3>Connection Error</h3>
        <p>{error}</p>
        <button onClick={() => setError(null)}>Try Again</button>
      </div>
    );
  }

  return (
    <Web3ReactProvider getLibrary={getLibrary}>{children}</Web3ReactProvider>
  );
}
