import { useQuery } from '@tanstack/react-query';
import { estateMindApi } from '@/shared/api/estateMindApi';
import { Box, LinearProgress, Stack, Typography } from '@mui/material';
import { formatCurrencyTND } from '@/shared/utils/format';

export function TopExpensiveLocations() {
  const q = useQuery({ queryKey: ['avgPriceByCity'], queryFn: estateMindApi.avgPriceByCity, refetchInterval: 60_000 });

  if (q.isLoading) return <LinearProgress />;
  if (q.isError)
    return (
      <Typography variant="body2" color="text.secondary">
        Données indisponibles (endpoint `/api/scraped-data/avg-price-city`).
      </Typography>
    );

  const rows = (q.data || []).slice(0, 5);

  return (
    <Stack spacing={1.25}>
      {rows.map((r) => (
        <Box key={r.city} sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 800 }}>
            {r.city}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 800 }}>
            {formatCurrencyTND(r.avgPrice)}
          </Typography>
        </Box>
      ))}
    </Stack>
  );
}

