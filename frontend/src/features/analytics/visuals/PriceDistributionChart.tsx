import { useQuery } from '@tanstack/react-query';
import { estateMindApi } from '@/shared/api/estateMindApi';
import { Box, LinearProgress, Typography } from '@mui/material';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export function PriceDistributionChart() {
  const q = useQuery({ queryKey: ['prices'], queryFn: estateMindApi.prices, refetchInterval: 60_000 });

  if (q.isLoading) return <LinearProgress />;
  if (q.isError)
    return (
      <Typography variant="body2" color="text.secondary">
        Données indisponibles (endpoint `/api/scraped-data/prices`).
      </Typography>
    );

  return (
    <Box sx={{ height: 260 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={q.data || []} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="range" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="count" stroke="#10b981" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
}

