import { useQuery } from '@tanstack/react-query';
import { estateMindApi } from '@/shared/api/estateMindApi';
import { Box, LinearProgress, Typography } from '@mui/material';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export function PriceByCityChart() {
  const q = useQuery({ queryKey: ['avgPriceByCity'], queryFn: estateMindApi.avgPriceByCity, refetchInterval: 60_000 });

  if (q.isLoading) return <LinearProgress />;
  if (q.isError)
    return (
      <Typography variant="body2" color="text.secondary">
        Données indisponibles (endpoint `/api/scraped-data/avg-price-city`).
      </Typography>
    );

  const data = (q.data || []).map((r) => ({ city: r.city, avgPrice: r.avgPrice }));

  return (
    <Box sx={{ height: 320 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="city" tick={{ fontSize: 12 }} interval={0} angle={-15} height={50} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="avgPrice" fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
}

