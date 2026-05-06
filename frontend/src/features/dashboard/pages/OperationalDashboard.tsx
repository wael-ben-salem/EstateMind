import { Box, Card, CardContent, Grid, Stack, Typography } from '@mui/material';
import { PageHeader } from '@/shared/ui/PageHeader';
import { PipelineRunPanel } from '@/features/pipeline/components/PipelineRunPanel';
import { DataFreshnessCard } from '@/features/data-market/components/DataFreshnessCard';
import { ErrorRateCard } from '@/features/monitoring/components/ErrorRateCard';

export function OperationalDashboard() {
  return (
    <Box>
      <PageHeader
        title="Operational Dashboard"
        subtitle="Pilotage opérationnel: exécutions, erreurs, fraîcheur et alertes."
      />

      <Grid container spacing={2}>
        <Grid item xs={12} lg={8}>
          <PipelineRunPanel />
        </Grid>
        <Grid item xs={12} lg={4}>
          <Stack spacing={2}>
            <DataFreshnessCard />
            <ErrorRateCard />
          </Stack>
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mt: 0 }}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 800 }}>
                Alerting (à brancher)
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                Cette vue est prête pour recevoir les événements temps réel via Socket.io (pipeline.progress,
                quality.update, alert.triggered). Pour l’instant: mode “polling” via l’API existante.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

