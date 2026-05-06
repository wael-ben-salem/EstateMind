import { Box, Card, CardContent, LinearProgress, Stack, Typography } from '@mui/material';
import { PageHeader } from '@/shared/ui/PageHeader';
import { useQuery } from '@tanstack/react-query';
import { estateMindApi } from '@/shared/api/estateMindApi';

export function SystemHealth() {
  const health = useQuery({ queryKey: ['health'], queryFn: estateMindApi.health, refetchInterval: 15_000 });

  return (
    <Box>
      <PageHeader title="System Health" subtitle="Santé des services (backend + Airflow)." />
      <Card>
        <CardContent>
          {health.isLoading ? <LinearProgress /> : null}
          <Stack spacing={1} sx={{ mt: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 800 }}>
              Backend: {health.data?.status || (health.isError ? 'UNAVAILABLE' : '…')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Pour Airflow: le backend expose `GET /health/airflow` (à afficher ici ensuite).
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}

