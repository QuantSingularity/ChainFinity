import { useEffect, useState } from "react";

const Portfolio = ({ fetchData }) => {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        // Simulate API call if fetchData is not provided for tests
        const result = fetchData
          ? await fetchData()
          : [
              { id: "1", name: "Bitcoin", value: 50000, symbol: "BTC" },
              { id: "2", name: "Ethereum", value: 3000, symbol: "ETH" },
            ];
        setData(result);
      } catch (_err) {
        setError("Failed to fetch portfolio data");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [fetchData]);

  const handleSortByName = () => {
    if (data) {
      const sortedData = [...data].sort((a, b) => a.name.localeCompare(b.name));
      setData(sortedData);
    }
  };

  const handleSortByValue = () => {
    if (data) {
      const sortedData = [...data].sort((a, b) => b.value - a.value);
      setData(sortedData);
    }
  };

  const filteredData = data
    ? data.filter((token) =>
        token.name.toLowerCase().includes(searchTerm.toLowerCase()),
      )
    : [];

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h2>Portfolio Value: {/* Placeholder for actual value */}</h2>
      <input
        type="text"
        placeholder="Search tokens"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <button onClick={handleSortByName}>Sort by name</button>
      <button onClick={handleSortByValue}>Sort by value</button>
      {filteredData.length > 0 ? (
        <ul>
          {filteredData.map((token) => (
            <li key={token.id}>
              {token.name} ({token.symbol}): ${token.value}
            </li>
          ))}
        </ul>
      ) : (
        <p>No tokens found.</p>
      )}
    </div>
  );
};

export default Portfolio;
