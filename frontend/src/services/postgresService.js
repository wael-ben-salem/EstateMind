const API_BASE_URL = '/api';

export const postgresService = {
  getScrapedStats: async () => {
    const response = await fetch(`${API_BASE_URL}/scraped-data/stats`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return await response.json();
  },

  getLocationDistribution: async () => {
    const response = await fetch(`${API_BASE_URL}/scraped-data/locations`);
    if (!response.ok) throw new Error('Failed to fetch location distribution');
    return await response.json();
  },

  getPropertyTypes: async () => {
    const response = await fetch(`${API_BASE_URL}/scraped-data/property-types`);
    if (!response.ok) throw new Error('Failed to fetch property types');
    return await response.json();
  },

  getTransactionTypes: async () => {
    const response = await fetch(`${API_BASE_URL}/scraped-data/transactions`);
    if (!response.ok) throw new Error('Failed to fetch transaction types');
    return await response.json();
  },

  getPriceDistribution: async () => {
    const response = await fetch(`${API_BASE_URL}/scraped-data/prices`);
    if (!response.ok) throw new Error('Failed to fetch price distribution');
    return await response.json();
  },

  getAvgPriceByCity: async () => {
    const response = await fetch(`${API_BASE_URL}/scraped-data/avg-price-city`);
    if (!response.ok) throw new Error('Failed to fetch average price by city');
    return await response.json();
  },
};