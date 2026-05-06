import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const LocationChart = ({ data }) => {
  const chartData = data || [
    { location: 'Tunis', count: 3500 },
    { location: 'Sfax', count: 2100 },
    { location: 'Sousse', count: 1850 },
    { location: 'Ariana', count: 1600 },
    { location: 'Monastir', count: 980 }
  ];

  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="location" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="count" fill="#1890ff" name="Properties" />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default LocationChart;
