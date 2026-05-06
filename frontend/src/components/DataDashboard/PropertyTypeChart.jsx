import React from 'react';
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts';

const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1'];

const PropertyTypeChart = ({ data }) => {
  const chartData = data || [
    { name: 'Apartment', value: 5400 },
    { name: 'House', value: 3200 },
    { name: 'Villa', value: 2100 },
    { name: 'Studio', value: 1800 },
    { name: 'Land', value: 930 }
  ];

  return (
    <ResponsiveContainer width="100%" height={400}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, value }) => `${name}: ${value}`}
          outerRadius={120}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default PropertyTypeChart;
