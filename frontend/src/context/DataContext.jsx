import React, { createContext, useState, useEffect } from 'react';

export const DataContext = createContext();

export const DataProvider = ({ children }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchScrapedData = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/scraped-data/stats');
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScrapedData();
    const interval = setInterval(fetchScrapedData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <DataContext.Provider value={{
      data,
      loading,
      error,
      refetch: fetchScrapedData
    }}>
      {children}
    </DataContext.Provider>
  );
};
