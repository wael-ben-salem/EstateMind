import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const PriceDistributionChart = ({ data }) => {
  const chartData = data || [
    { range: '<10K', count: 1200 },
    { range: '10K-30K', count: 3400 },
    { range: '30K-60K', count: 4500 },
    { range: '60K-100K', count: 2900 },
    { range: '>100K', count: 1830 }
  ];

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="range" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="count" stroke="#52c41a" strokeWidth={2} name="Properties" />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default PriceDistributionChart;
